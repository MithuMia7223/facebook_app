import json
import queue
import requests
from tkinter import Button, Entry, Frame, Label, messagebox
import config

messages = queue.Queue()

PAGE = 1
LIMIT = 5
SEARCH_QUERY = ""


# ================= API =================


def api_request(method, url, **kwargs):
    try:
        return requests.request(
            method, f"{config.API_BASE_URL}{url}", timeout=5, **kwargs
        )
    except Exception as e:
        messagebox.showerror("API Error", str(e))


def api_get(url, params=None):
    return api_request("GET", url, params=params)


def api_post(url, data=None, auth=None):
    return api_request("POST", url, json=data, auth=auth)


def api_put(url, data=None, auth=None):
    return api_request("PUT", url, json=data, auth=auth)


def api_delete(url, auth=None):
    return api_request("DELETE", url, auth=auth)


# ================= AUTH =================


def _auth_tuple():
    user = getattr(config, "signed_in_username", "")
    pwd = getattr(config, "signed_in_password", "")
    return (user, pwd) if user and pwd else None


# ================= MAIN =================


def build_posts(posts_page, posts_container, new_post_entry):

    global PAGE, SEARCH_QUERY

    # ================= CLEAR =================
    def clear_posts():
        for w in posts_container.winfo_children():
            w.destroy()

    # ================= LOAD POSTS =================
    def load_posts():
        res = api_get("/posts/", {"page": PAGE, "limit": LIMIT, "search": SEARCH_QUERY})

        if not res or res.status_code != 200:
            return messagebox.showerror("Posts", "Failed loading posts")

        clear_posts()

        data = res.json()
        if isinstance(data, dict):
            data = data.get("posts", [])

        for p in data:
            create_post_card(p)

    # ================= POST CARD =================
    def create_post_card(p):
        post_id = p.get("id")

        frame = Frame(posts_container, bd=1, relief="solid", padx=10, pady=5)
        frame.pack(fill="x", pady=5)

        Label(frame, text=p.get("content", ""), font=("Arial", 12)).pack(anchor="w")
        Label(frame, text=f"👤 {p.get('author','Unknown')}").pack(anchor="w")

        like_label = Label(frame, text=f"👍 {p.get('likes_count',0)}")
        like_label.pack(anchor="w")

        comment_label = Label(frame, text=f"💬 {p.get('comments_count',0)}")
        comment_label.pack(anchor="w")

        liked = False

        # ================= LIKE / UNLIKE =================
        def toggle_like():
            nonlocal liked

            auth = _auth_tuple()
            if not auth:
                return messagebox.showwarning("Auth", "Login required")

            if not liked:
                res = api_post(f"/posts/{post_id}/likes", {}, auth)

                if res and res.status_code in (200, 201):
                    liked = True
                    new_count = int(p.get("likes_count", 0)) + 1
                    p["likes_count"] = new_count
                    like_label.config(text=f"👍 {new_count}")

            else:
                res = api_delete(f"/posts/{post_id}/likes", auth)

                if res and res.status_code == 200:
                    liked = False
                    new_count = max(0, int(p.get("likes_count", 0)) - 1)
                    p["likes_count"] = new_count
                    like_label.config(text=f"👍 {new_count}")

        # ================= COMMENT =================
        def comment_post():
            auth = _auth_tuple()
            if not auth:
                return messagebox.showwarning("Auth", "Login required")

            text = comment_entry.get().strip()
            if not text:
                return messagebox.showwarning("Comment", "Write comment first")

            res = api_post(f"/comments/posts/{post_id}", {"content": text}, auth)

            if res and res.status_code in (200, 201):
                comment_entry.delete(0, "end")

                new_count = int(p.get("comments_count", 0)) + 1
                p["comments_count"] = new_count
                comment_label.config(text=f"💬 {new_count}")

        # ================= EDIT =================
        def edit_post():
            auth = _auth_tuple()
            if not auth:
                return

            text = new_post_entry.get().strip()
            if not text:
                return

            res = api_put(f"/posts/{post_id}", {"content": text}, auth)
            if res and res.status_code == 200:
                load_posts()

        # ================= DELETE =================
        def delete_post():
            auth = _auth_tuple()
            if not auth:
                return

            res = api_delete(f"/posts/{post_id}", auth)
            if res and res.status_code == 200:
                load_posts()

        # ================= BUTTONS =================
        btn = Frame(frame)
        btn.pack(anchor="w", pady=5)

        Button(btn, text="Like ❤️ / Unlike 💔", command=toggle_like).pack(
            side="left", padx=5
        )
        Button(btn, text="Comment 💬", command=comment_post).pack(side="left", padx=5)
        Button(btn, text="Edit ✏️", command=edit_post).pack(side="left", padx=5)
        Button(btn, text="Delete 🗑", command=delete_post).pack(side="left", padx=5)

        # ================= COMMENT INPUT =================
        comment_box = Frame(frame)
        comment_box.pack(anchor="w", pady=5)

        comment_entry = Entry(comment_box, width=40)
        comment_entry.pack(side="left", padx=5)

    # ================= CREATE POST =================
    def create_post():
        auth = _auth_tuple()
        content = new_post_entry.get().strip()

        if not auth:
            return messagebox.showwarning("Auth", "Login required")

        if not content:
            return messagebox.showwarning("Post", "Empty post")

        res = api_post("/posts/", {"content": content}, auth)

        if res and res.status_code in (200, 201):
            new_post_entry.delete(0, "end")
            load_posts()

    # ================= SEARCH =================
    def search_posts():
        global SEARCH_QUERY, PAGE
        SEARCH_QUERY = search_entry.get().strip()
        PAGE = 1
        load_posts()

    # ================= PAGINATION =================
    def next_page():
        global PAGE
        PAGE += 1
        load_posts()

    def prev_page():
        global PAGE
        if PAGE > 1:
            PAGE -= 1
        load_posts()

    # ================= UI =================
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

    # INIT LOAD
    load_posts()

    # ================= SOCKET =================
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
