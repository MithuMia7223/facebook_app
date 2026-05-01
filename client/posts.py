import json
import queue
import requests
from tkinter import Button, Entry, Frame, Label, Toplevel, messagebox
import config

messages = queue.Queue()

PAGE = 1
LIMIT = 5
SEARCH_QUERY = ""


def api_request(method, url, **kwargs):
    try:
        return requests.request(
            method, f"{config.API_BASE_URL}{url}", timeout=5, **kwargs
        )
    except Exception as e:
        messagebox.showerror("API Error", str(e))
        return None


def api_get(url, params=None):
    return api_request("GET", url, params=params)


def api_post(url, data=None, auth=None):
    return api_request("POST", url, json=data, auth=auth)


def api_patch(url, data=None, auth=None):
    return api_request("PATCH", url, json=data, auth=auth)


def api_delete(url, auth=None):
    return api_request("DELETE", url, auth=auth)


def _auth_tuple():
    user = getattr(config, "signed_in_username", "")
    pwd = getattr(config, "signed_in_password", "")
    return (user, pwd) if user and pwd else None


def build_posts(posts_page, posts_container, new_post_entry):

    global PAGE, SEARCH_QUERY

    def clear_posts():
        for w in posts_container.winfo_children():
            w.destroy()

    def load_posts():
        res = api_get("/posts/", {"page": PAGE, "limit": LIMIT, "search": SEARCH_QUERY})

        if not res or res.status_code != 200:
            return messagebox.showerror("Posts", "Failed loading posts")

        clear_posts()

        data = res.json()
        if isinstance(data, dict):
            data = data.get("posts", [])

        if not data:
            Label(posts_container, text="No posts found 😔").pack()
            return

        for p in data:
            create_post_card(p)

    def open_post_detail(p):
        win = Toplevel()
        win.title("Post Details")

        Label(win, text=p.get("content"), font=("Arial", 14)).pack()
        Label(win, text=f"👤 {p.get('author','Unknown')}").pack()
        Label(win, text=f"📅 {p.get('created_at','')}").pack()
        Label(win, text=f"👍 Likes: {p.get('likes_count',0)}").pack()
        Label(win, text=f"💬 Comments: {p.get('comment_count',0)}").pack()

    def open_comments(post_id):
        win = Toplevel()
        win.title("Comments")

        res = api_get(f"/comments/posts/{post_id}")

        if not res or res.status_code != 200:
            Label(win, text="No comments found").pack()
            return

        data = res.json()
        print("comments data: ")
        print(data)

        if isinstance(data, dict):
            data = data.get("data", [])

        if not data:
            Label(win, text="No comments").pack()
            return

        for c in data:
            cid = c.get("id")

            comment_frame = Frame(win, bd=1, relief="solid", padx=5, pady=5)
            comment_frame.pack(fill="x", pady=5)

            Label(
                comment_frame,
                text=f"{c.get('author_id','Unknown')} : {c.get('content','')}",
            ).pack(anchor="w")

            like_label = Label(comment_frame, text=f"👍 {c.get('likes_count',0)}")
            like_label.pack(anchor="w")

            def like_comment(comment_id=cid, label=like_label):
                auth = _auth_tuple()
                if not auth:
                    return

                res = api_post(f"/comments/{comment_id}/like", {}, auth)

                if res and res.status_code in (200, 201):
                    current = c.get("likes_count", 0)
                    c["likes_count"] = current + 1
                    label.config(text=f"👍 {current + 1}")

            reply_box = Frame(comment_frame)
            reply_box.pack(anchor="w", pady=3)

            reply_entry = Entry(reply_box, width=30)
            reply_entry.pack(side="left", padx=5)

            def reply_comment(comment_id=cid, entry=reply_entry):
                auth = _auth_tuple()
                if not auth:
                    return

                text = entry.get().strip()
                if not text:
                    return

                res = api_post(f"/comments/{comment_id}/reply", {"content": text}, auth)

                if res and res.status_code in (200, 201):
                    entry.delete(0, "end")
                    messagebox.showinfo("Reply", "Reply added")

            btns = Frame(comment_frame)
            btns.pack(anchor="w")

            Button(btns, text="Like 👍", command=like_comment).pack(side="left", padx=5)
            Button(btns, text="Reply 💬", command=reply_comment).pack(
                side="left", padx=5
            )

    def create_post_card(p):
        post_id = p.get("id")

        frame = Frame(posts_container, bd=1, relief="solid", padx=10, pady=8)
        frame.pack(fill="x", pady=5)

        Label(frame, text=p.get("content", ""), font=("Arial", 12, "bold")).pack(
            anchor="w"
        )
        Label(
            frame, text=f"👤 {p.get('author','Unknown')} | 📅 {p.get('created_at','')}"
        ).pack(anchor="w")

        like_label = Label(frame, text=f"👍 {p.get('likes_count',0)}")
        like_label.pack(anchor="w")

        comment_label = Label(frame, text=f"💬 {p.get('comment_count',0)}")
        comment_label.pack(anchor="w")

        liked = p.get("is_liked", False)

        def toggle_like():
            nonlocal liked

            auth = _auth_tuple()
            if not auth:
                return messagebox.showwarning("Auth", "Login required")

            if not liked:
                res = api_post(f"/posts/{post_id}/likes", {}, auth)
                if res and res.status_code in (200, 201):
                    liked = True
                    p["likes_count"] = p.get("likes_count", 0) + 1
                    like_label.config(text=f"👍 {p['likes_count']}")
            else:
                res = api_delete(f"/posts/{post_id}/likes", auth)
                if res and res.status_code == 200:
                    liked = False
                    p["likes_count"] = max(0, p.get("likes_count", 0) - 1)
                    like_label.config(text=f"👍 {p['likes_count']}")

        def comment_post():
            auth = _auth_tuple()
            if not auth:
                return

            text = comment_entry.get().strip()
            if not text:
                return

            res = api_post(f"/comments/posts/{post_id}", {"content": text}, auth)

            if res and res.status_code in (200, 201):
                comment_entry.delete(0, "end")
                p["comment_count"] = p.get("comment_count", 0) + 1
                comment_label.config(text=f"💬 {p['comment_count']}")

        def enter_comment(event):
            comment_post()

        def edit_post():
            auth = _auth_tuple()
            if not auth:
                return

            popup = Toplevel()
            popup.title("Edit Post")

            edit_entry = Entry(popup, width=40)
            edit_entry.insert(0, p.get("content", ""))
            edit_entry.pack()

            def save():
                text = edit_entry.get().strip()
                res = api_patch(f"/posts/{post_id}", {"content": text}, auth)

                if res and res.status_code == 200:
                    popup.destroy()
                    load_posts()

            Button(popup, text="Save", command=save).pack()

        def delete_post():
            auth = _auth_tuple()
            if not auth:
                return

            res = api_delete(f"/posts/{post_id}", auth)
            if res and res.status_code == 200:
                load_posts()

        btn = Frame(frame)
        btn.pack(anchor="w", pady=5)

        Button(btn, text="Like ❤️", command=toggle_like).pack(side="left")
        Button(btn, text="Edit ✏️", command=edit_post).pack(side="left")
        Button(btn, text="Delete 🗑", command=delete_post).pack(side="left")
        Button(btn, text="View 🔍", command=lambda: open_post_detail(p)).pack(
            side="left"
        )
        Button(btn, text="Comments 💬", command=lambda: open_comments(post_id)).pack(
            side="left"
        )

        comment_box = Frame(frame)
        comment_box.pack(anchor="w")

        comment_entry = Entry(comment_box, width=40)
        comment_entry.pack(side="left", padx=5)
        comment_entry.bind("<Return>", enter_comment)

        Button(comment_box, text="Comment", command=comment_post).pack(side="left")

    def create_post():
        auth = _auth_tuple()
        content = new_post_entry.get().strip()

        if not content:
            return

        api_post("/posts/", {"content": content}, auth)
        load_posts()

    def search_posts():
        global SEARCH_QUERY, PAGE
        SEARCH_QUERY = search_entry.get().strip()
        PAGE = 1
        load_posts()

    def next_page():
        global PAGE
        PAGE += 1
        load_posts()

    def prev_page():
        global PAGE
        if PAGE > 1:
            PAGE -= 1
        load_posts()

    top = Frame(posts_page)
    top.pack(pady=5)

    Button(top, text="Create Post", command=create_post).pack(side="left")
    Button(top, text="Reload", command=load_posts).pack(side="left")

    search_frame = Frame(posts_page)
    search_frame.pack()

    search_entry = Entry(search_frame)
    search_entry.pack(side="left")

    Button(search_frame, text="Search", command=search_posts).pack(side="left")

    nav = Frame(posts_page)
    nav.pack()

    Button(nav, text="Prev", command=prev_page).pack(side="left")
    Button(nav, text="Next", command=next_page).pack(side="left")
    load_posts()

    def poll_messages():
        try:
            msg = messages.get_nowait()
            data = json.loads(msg)
            if data.get("event") == "post:new":
                load_posts()
        except:
            pass

        posts_page.after(100, poll_messages)

    posts_page.after(100, poll_messages)
