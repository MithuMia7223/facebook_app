from tkinter import Button, Entry, Frame, Label, messagebox
import requests

import config


def _auth_tuple():
    # Read logged-in credentials saved during login.
    user = getattr(config, "signed_in_username", "")
    pwd = getattr(config, "signed_in_password", "")
    if not user or not pwd:
        return None
    return (user, pwd)


def build_posts(posts_page, posts_table, new_post_entry):
    def _get_selected_post_id():
        # 1) Try normal row selection
        selected = posts_table.selection()
        if selected:
            return selected[0]

        # 2) Fallback: focused row
        focused = posts_table.focus()
        if focused:
            posts_table.selection_set(focused)
            return focused

        # 3) Fallback: first row in table
        rows = posts_table.get_children()
        if rows:
            first = rows[0]
            posts_table.selection_set(first)
            posts_table.focus(first)
            return first

        return None

    def clear_posts_table():
        # Remove all existing rows before reloading fresh data from API.
        for item in posts_table.get_children():
            posts_table.delete(item)

    def _get_comment_count(post_id):
        try:
            r = requests.get(f"{config.API_BASE_URL}/comments/posts/{post_id}")
            if r.status_code != 200:
                return 0
            return r.json().get("total", 0)
        except Exception:
            return 0

    def load_posts_table():
        try:
            r = requests.get(f"{config.API_BASE_URL}/posts/")
            if r.status_code != 200:
                clear_posts_table()
                if r.status_code == 404:
                    return
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

        # Get typed post content from Entry widget.
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
            messagebox.showwarning("Posts", "No posts found. Click Load Posts first.")
            return

        try:
            r = requests.post(f"{config.API_BASE_URL}/posts/{post_id}/likes", auth=auth)
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
            messagebox.showwarning("Posts", "No posts found. Click Load Posts first.")
            return

        # Prefer dedicated comment box; fallback to post input for convenience.
        comment_text = comment_entry.get().strip() or new_post_entry.get().strip()
        if not comment_text:
            messagebox.showwarning(
                "Posts",
                "Comment is empty. Type in Comment box (or Post box) first.",
            )
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

    actions = Frame(posts_page)
    actions.pack(pady=5)

    Button(actions, text="Create Post", command=create_post).pack(side="left", padx=5)
    Button(actions, text="Like Selected", command=like_selected_post).pack(
        side="left", padx=5
    )
    Button(actions, text="Comment", command=add_comment_to_selected_post).pack(
        side="left", padx=5
    )
    Button(actions, text="Load Posts", command=load_posts_table).pack(
        side="left", padx=5
    )

    comment_box = Frame(posts_page)
    comment_box.pack(pady=5)
    Label(comment_box, text="Comment").pack(side="left", padx=5)
    comment_entry = Entry(comment_box, width=45)
    comment_entry.pack(side="left", padx=5)
