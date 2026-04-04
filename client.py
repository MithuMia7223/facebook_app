from tkinter import *
from tkinter import ttk, messagebox
import requests

main = Tk()
main.title("Social App")
main.geometry("900x650")

fb = ttk.Notebook(main)
fb.pack(fill="both", expand=True)

signed_in_username = None
signed_in_password = None
signed_in_user_id = None


login_page = ttk.Frame(fb)
fb.add(login_page, text="Login")

Label(login_page, text="Username").pack(pady=5)
username_entry = Entry(login_page)
username_entry.pack()

Label(login_page, text="Password").pack(pady=5)
password_entry = Entry(login_page, show="*")
password_entry.pack()


signup_page = ttk.Frame(fb)
fb.add(signup_page, text="Signup")

signup_username = Entry(signup_page)
signup_password = Entry(signup_page, show="*")
signup_name = Entry(signup_page)
signup_bio = Entry(signup_page)

for text, widget in [
    ("Username", signup_username),
    ("Password", signup_password),
    ("Name", signup_name),
    ("Bio", signup_bio),
]:
    Label(signup_page, text=text).pack(pady=5)
    widget.pack()


def signup():
    try:
        r = requests.post(
            "http://localhost:8000/users",
            json={
                "username": signup_username.get(),
                "password": signup_password.get(),
                "name": signup_name.get(),
                "bio": signup_bio.get(),
            },
        )
        if r.status_code in [200, 201]:
            messagebox.showinfo("Success", "Signup done")
            fb.select(login_page)
        else:
            messagebox.showerror("Error", r.text)
    except Exception as e:
        messagebox.showerror("Error", str(e))


Button(signup_page, text="Signup", command=signup).pack(pady=10)


profile_page = ttk.Frame(fb)
profile_text = Text(profile_page, height=10)


def load_profile():
    try:
        r = requests.get(
            "http://localhost:8000/users/me",
            auth=(signed_in_username, signed_in_password),
        )

        if r.status_code != 200:
            messagebox.showerror("Error", "Failed to load profile")
            return

        data = r.json()

        profile_text.delete("1.0", END)
        profile_text.insert(END, f"ID: {data.get('id')}\n")
        profile_text.insert(END, f"Username: {data.get('username')}\n")
        profile_text.insert(END, f"Name: {data.get('name')}\n")
        profile_text.insert(END, f"Bio: {data.get('bio')}\n")

    except Exception as e:
        messagebox.showerror("Error", str(e))


def logout():
    global signed_in_username, signed_in_password, signed_in_user_id

    signed_in_username = None
    signed_in_password = None
    signed_in_user_id = None

    fb.forget(profile_page)
    fb.forget(posts_page)
    fb.forget(friends_page)

    fb.add(login_page, text="Login")
    fb.add(signup_page, text="Signup")

    fb.select(login_page)


posts_page = ttk.Frame(fb)

new_post_entry = Entry(posts_page, width=50)
new_post_entry.pack(pady=10)


def create_post():
    content = new_post_entry.get().strip()

    if not content:
        messagebox.showerror("Error", "Post cannot be empty")
        return

    try:
        r = requests.post(
            "http://localhost:8000/posts",
            json={"content": content},
            auth=(signed_in_username, signed_in_password),
        )

        if r.status_code in [200, 201]:
            messagebox.showinfo("Post", "Created")
            new_post_entry.delete(0, END)
            load_posts_table()
        else:
            messagebox.showerror("Error", "Failed to create post")

    except Exception as e:
        messagebox.showerror("Post", str(e))


Button(posts_page, text="Create Post", command=create_post).pack()

posts_table = ttk.Treeview(
    posts_page, columns=("Content", "Likes", "Comment"), show="headings"
)

posts_table.heading("Content", text="Content")
posts_table.heading("Likes", text="Likes")
posts_table.pack(fill="both", expand=True)


def load_posts_table():
    for row in posts_table.get_children():
        posts_table.delete(row)

    r = requests.get(
        "http://localhost:8000/posts",
        auth=(signed_in_username, signed_in_password),
    )

    if r.status_code != 200:
        messagebox.showerror("Error", "Failed to load posts")
        return

    for post in r.json():
        posts_table.insert(
            "",
            END,
            iid=(post["id"]),
            values=(post["content"], post.get("likes_count", 0), "Comment"),
        )


def like_post(post_id):
    requests.post(
        f"http://localhost:8000/posts/{post_id}/likes",
        auth=(signed_in_username, signed_in_password),
    )
    load_posts_table()


def like_selected_post():
    selected = posts_table.selection()
    if not selected:
        messagebox.showerror("Error", "Select a post")
        return

    like_post(selected[0])


def open_comment_popup():
    selected = posts_table.selection()
    if not selected:
        messagebox.showerror("Error", "Select a post")
        return

    post_id = selected[0]

    win = Toplevel(main)
    win.title("Comment")

    entry = Entry(win)
    entry.pack(5)

    def submit():
        requests.post(
            f"http://localhost:8000/comments/posts/{post_id}",
            json={"content": entry.get()},
            auth=(signed_in_username, signed_in_password),
        )
        messagebox.showinfo("Success", "Comment added")

        win.destroy()

    Button(win, text="Submit", command=submit).pack(pady=5)


Button(posts_page, text="Like Selected Post", command=like_selected_post).pack(pady=5)
Button(posts_page, text="Comment", command=open_comment_popup).pack(pady=5)
Button(posts_page, text="Load Posts", command=load_posts_table).pack(pady=5)

friends_page = ttk.Frame(fb)

main_frame = Frame(friends_page)
main_frame.pack(fill="both", expand=True)


left_frame = Frame(main_frame)
left_frame.pack(side=LEFT, fill="both", expand=True, padx=10)

Label(left_frame, text="Friends").pack()

friends_table = ttk.Treeview(left_frame, columns=("ID", "Username"), show="headings")
friends_table.heading("ID", text="ID")
friends_table.heading("Username", text="Username")
friends_table.pack(fill="both", expand=True)


def load_friends():
    if not signed_in_user_id:
        messagebox.showerror("Error", "Login first")
        return

    try:
        r = requests.get(
            f"http://localhost:8000/users/{signed_in_user_id}/friends",
            auth=(signed_in_username, signed_in_password),
        )
        if r.status_code != 200:
            messagebox.showerror("Error", "Failed to load friends")
            return

        for row in friends_table.get_children():
            friends_table.delete(row)

        for f in r.json()["data"]:
            if isinstance(f, dict):
                fid = f.get("id")
                username = f.get("username")
            else:
                fid = f
                username = str(f)
            friends_table.insert(
                "",
                END,
                iid=str(fid),
                values=(fid, username),
            )

    except Exception as e:
        messagebox.showerror("Error", str(e))


def remove_friend():
    selected = friends_table.selection()

    if not selected:
        messagebox.showerror("Error", "Select a friend")
        return

    friend_id = selected[0]

    try:
        r = requests.delete(
            f"http://localhost:8000/users/{signed_in_user_id}/friends/{friend_id}",
            auth=(signed_in_username, signed_in_password),
        )
        if r.status_code in [200, 204]:
            messagebox.showerror("Success", "Friend removed")
            load_friends()
        else:
            messagebox.showerror("Error", "Failed to removed friend")

    except Exception as e:
        messagebox.showerror("Error", str(e))


Button(left_frame, text="Load Friends", command=load_friends).pack(pady=5)
Button(left_frame, text="Remove Friends", command=remove_friend).pack(pady=5)


right_frame = Frame(main_frame)
right_frame.pack(side=RIGHT, fill="y", padx=10)

Label(right_frame, text="Send Friend Request").pack(pady=5)

friend_entry = Entry(right_frame)
friend_entry.pack(pady=5)


def send_friend_request(event=None):
    recipient = friend_entry.get().strip()
    if not recipient:
        return

    try:
        r = requests.get(
            f"http://localhost:8000/users/username/{recipient}",
            auth=(signed_in_username, signed_in_password),
        )

        if r.status_code != 200:
            messagebox.showerror("Error", "User not found")
            return

        user_id = r.json()["id"]

        r2 = requests.post(
            f"http://localhost:8000/users/{signed_in_user_id}/friends/{user_id}",
            auth=(signed_in_username, signed_in_password),
        )

        if r2.status_code in [200, 201]:
            messagebox.showinfo("Success", "Request sent")
            friend_entry.delete(0, END)
        else:
            messagebox.showerror("Error", r2.text)

    except Exception as e:
        messagebox.showerror("Error", str(e))


friend_entry.bind("<Return>", send_friend_request)

Button(left_frame, text="Refresh", command=load_friends).pack(pady=5)


def login():
    global signed_in_username, signed_in_password, signed_in_user_id

    user = username_entry.get()
    pwd = password_entry.get()

    try:
        r = requests.get("http://localhost:8000/users/me", auth=(user, pwd))

        if r.status_code != 200:
            messagebox.showerror("Login", "Failed")
            return

        signed_in_username = user
        signed_in_password = pwd
        signed_in_user_id = r.json()["id"]

        fb.forget(login_page)
        fb.forget(signup_page)

        fb.add(profile_page, text="Profile")
        fb.add(posts_page, text="Posts")
        fb.add(friends_page, text="Friends")

        profile_text.pack(pady=10)

        Button(profile_page, text="Load Profile", command=load_profile).pack(pady=5)
        Button(profile_page, text="Logout", command=logout).pack(pady=5)

        fb.select(profile_page)

    except Exception as e:
        messagebox.showerror("Error", str(e))


Button(login_page, text="Login", command=login).pack(pady=10)

main.mainloop()

"""
add
commit
push / pull
"""
