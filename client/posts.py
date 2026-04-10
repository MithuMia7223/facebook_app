import json
import queue
from tkinter import Button, Entry, Frame, Label, messagebox, Toplevel, Text
import requests
import config

messages = queue.Queue()


def _auth_tuple():
    user = getattr(config, "signed_in_username", "")
    pwd = getattr(config, "signed_in_password", "")
    if not user or not pwd:
        return None
    return (user, pwd)


def build_posts(posts_page, posts_table, new_post_entry):

    def _get_selected_post_id():
        selected = posts_table.selection()
        if selected:
            return selected[0]

        focused = posts_table.focus()
        if focused:
            return focused

        rows = posts_table.get_children()
        if rows:
            first = rows[0]
            posts_table.selection_set(first)
            posts_table.focus(first)
            return first

        return None

    def clear_posts_table():
        for item in posts_table.get_children():
            posts_table.delete(item)

    def _get_comment_count(post_id):
        try:
            r = requests.get(f"{config.API_BASE_URL}/comments/posts/{post_id}")
            if r.status_code != 200:
                return 0
            return r.json().get("total", 0)
        except:
            return 0

    def load_posts_table():
        try:
            r = requests.get(f"{config.API_BASE_URL}/posts/")
            if r.status_code != 200:
                clear_posts_table()
                messagebox.showerror("Posts", r.text)
                return

            clear_posts_table()
            posts = r.json()

            for post in posts:
                post_id = str(post.get("id"))
                posts_table.insert(
                    "",
                    "end",
                    iid=post_id,
                    values=(
                        post.get("content", ""),
                        post.get("likes_count", 0),
                        _get_comment_count(post_id),
                    ),
                )

        except Exception as e:
            messagebox.showerror("Posts", str(e))

    def create_post():
        auth = _auth_tuple()
        if not auth:
            messagebox.showwarning("Posts", "Please login first")
            return

        content = new_post_entry.get().strip()
        if not content:
            messagebox.showwarning("Posts", "Post content is empty")
            return

        try:
            r = requests.post(
                f"{config.API_BASE_URL}/posts/",
                json={"content": content},
                auth=auth,
            )
            if r.status_code not in [200, 201]:
                messagebox.showerror("Posts", r.text)
                return

            new_post_entry.delete(0, "end")
            load_posts_table()

        except Exception as e:
            messagebox.showerror("Posts", str(e))

    def like_selected_post():
        auth = _auth_tuple()
        if not auth:
            messagebox.showwarning("Posts", "Please login first")
            return

        post_id = _get_selected_post_id()
        if not post_id:
            messagebox.showwarning("Posts", "Select a post first")
            return

        try:
            r = requests.post(
                f"{config.API_BASE_URL}/posts/{post_id}/likes",
                auth=auth,
            )
            if r.status_code not in [200, 201]:
                messagebox.showerror("Posts", r.text)
                return

            load_posts_table()

        except Exception as e:
            messagebox.showerror("Posts", str(e))

    def add_comment_to_selected_post():
        auth = _auth_tuple()
        if not auth:
            messagebox.showwarning("Posts", "Please login first")
            return

        post_id = _get_selected_post_id()
        if not post_id:
            messagebox.showwarning("Posts", "Select a post first")
            return

        comment_text = comment_entry.get().strip() or new_post_entry.get().strip()
        if not comment_text:
            messagebox.showwarning("Posts", "Comment is empty")
            return

        try:
            r = requests.post(
                f"{config.API_BASE_URL}/comments/posts/{post_id}",
                json={"content": comment_text},
                auth=auth,
            )
            if r.status_code not in [200, 201]:
                messagebox.showerror("Posts", r.text)
                return

            comment_entry.delete(0, "end")
            load_posts_table()

        except Exception as e:
            messagebox.showerror("Posts", str(e))

    # ================= VIEW DETAILS =================
    def view_details():
        post_id = _get_selected_post_id()
        if not post_id:
            messagebox.showwarning("Posts", "Select a post first")
            return

        try:
            post_res = requests.get(f"{config.API_BASE_URL}/posts/{post_id}")
            if post_res.status_code != 200:
                messagebox.showerror("Posts", post_res.text)
                return

            post = post_res.json()

            win = Toplevel(posts_page)
            win.title(f"Post Details - {post_id}")
            win.geometry("550x500")

            Label(win, text="Post Content:", font=("Arial", 10, "bold")).pack(anchor="w")

            content_box = Text(win, height=4, wrap="word")
            content_box.pack(fill="x", padx=5)
            content_box.insert("end", post.get("content", ""))
            content_box.config(state="disabled")

            Label(win, text=f"❤️ Likes: {post.get('likes_count', 0)}").pack(anchor="w", pady=5)

            display_box = Text(win, wrap="word")
            display_box.pack(fill="both", expand=True, padx=5, pady=5)

            def load_likes():
                display_box.config(state="normal")
                display_box.delete("1.0", "end")

                try:
                    r = requests.get(f"{config.API_BASE_URL}/posts/{post_id}")
                    if r.status_code == 200:
                        data = r.json()

                        display_box.insert("end", "❤️ LIKES INFO\n\n")
                        display_box.insert("end", f"Total Likes: {data.get('likes_count', 0)}\n\n")
                        display_box.insert("end", str(data.get("likes", [])))
                    else:
                        display_box.insert("end", "Failed to load likes")

                except Exception as e:
                    display_box.insert("end", str(e))

                display_box.config(state="disabled")

            def load_comments():
                display_box.config(state="normal")
                display_box.delete("1.0", "end")

                try:
                    r = requests.get(f"{config.API_BASE_URL}/comments/posts/{post_id}")

                    if r.status_code == 200:
                        data = r.json()

                        if isinstance(data, list):
                            comments = data
                        else:
                            comments = data.get("comments", [])

                        display_box.insert("end", "💬 COMMENTS INFO\n\n")

                        if not comments:
                            display_box.insert("end", "No comments yet")
                        else:
                            for c in comments:
                                display_box.insert("end", f"- {c.get('content','')}\n")
                    else:
                        display_box.insert("end", "Failed to load comments")

                except Exception as e:
                    display_box.insert("end", str(e))

                display_box.config(state="disabled")

            btn_frame = Frame(win)
            btn_frame.pack(pady=5)

            Button(btn_frame, text="Load Likes ❤️", command=load_likes).pack(side="left", padx=10)
            Button(btn_frame, text="Load Comments 💬", command=load_comments).pack(side="left", padx=10)

        except Exception as e:
            messagebox.showerror("Posts", str(e))

    actions = Frame(posts_page)
    actions.pack(pady=5)

    Button(actions, text="Create Post", command=create_post).pack(side="left", padx=5)
    Button(actions, text="Like Selected", command=like_selected_post).pack(side="left", padx=5)
    Button(actions, text="Comment", command=add_comment_to_selected_post).pack(side="left", padx=5)
    Button(actions, text="Load Posts", command=load_posts_table).pack(side="left", padx=5)
    Button(actions, text="View Details", command=view_details).pack(side="left", padx=5)

    comment_box = Frame(posts_page)
    comment_box.pack(pady=5)

    Label(comment_box, text="Comment").pack(side="left", padx=5)
    comment_entry = Entry(comment_box, width=45)
    comment_entry.pack(side="left", padx=5)

    def handle_events(event, data):
        if event == "post:new":
            load_posts_table()

    def poll_messages():
        try:
            message = messages.get_nowait()
        except:
            posts_page.after(100, poll_messages)
            return

        try:
            payload = json.loads(message)
            handle_events(payload.get("event"), payload.get("data"))
        except:
            pass

        posts_page.after(100, poll_messages)

    posts_page.after(100, poll_messages)