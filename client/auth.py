from tkinter import *
from tkinter import ttk, messagebox
import requests
import config
from PIL import Image


def build_auth(
    fb,
    login_page,
    signup_page,
    profile_page,
    posts_page,
    friends_page,
    main,
    profile_text,
    load_profile,
    load_posts_table,
    load_friends,
):

    username_entry = Entry(login_page)
    password_entry = Entry(login_page, show="*")

    Label(login_page, text="Username").pack(pady=5)
    username_entry.pack()

    Label(login_page, text="Password").pack(pady=5)
    password_entry.pack()

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
                f"{config.API_BASE_URL}/users",
                json={
                    "username": signup_username.get(),
                    "password": signup_password.get(),
                    "name": signup_name.get(),
                    "bio": signup_bio.get(),
                },
            )
            if r.status_code in [200, 201]:
                messagebox.showinfo("Success", "Signup successful")
                fb.select(login_page)
            else:
                messagebox.showerror("Error", r.text)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_image(url, filename):
        try:
            res = requests.get(url)
            if "image" in res.headers.get("Content-Type", ""):
                with open(filename, "wb") as f:
                    f.write(res.content)
                return Image.open(filename)
            else:
                print("Not a valid image:", url)
        except Exception as e:
            print("Image error:", e)
        return None

    def login():
        user = username_entry.get()
        pwd = password_entry.get()

        if not user or not pwd:
            messagebox.showwarning("Input Error", "Enter username & password")
            return

        print("Trying to login", user, pwd)

        try:
            r = requests.get(f"{config.API_BASE_URL}/users/me", auth=(user, pwd))
            print("Status:", r.status_code)
            print("Response:", r.text)

            if r.status_code != 200:
                messagebox.showerror("Login", "Failed")
                return

            data = r.json()
            print("User data:", data)

            config.signed_in_username = user
            config.signed_in_password = pwd
            config.signed_in_user_id = data.get("id")

            fb.forget(login_page)
            fb.forget(signup_page)

            fb.add(profile_page, text="Profile")
            fb.add(posts_page, text="Posts")
            fb.add(friends_page, text="Friends")

            fb.select(profile_page)

            BASE_URL = config.API_BASE_URL

            if data.get("avatar_url"):
                avatar_url = BASE_URL + data["avatar_url"]
                print("Avatar:", avatar_url)

                avatar_img = load_image(avatar_url, "avatar.jpg")
                if avatar_img:
                    avatar_img.show()

            if data.get("cover_url"):
                cover_url = BASE_URL + data["cover_url"]
                print("Cover:", cover_url)

                cover_img = load_image(cover_url, "cover.jpg")
                if cover_img:
                    cover_img.show()

        except Exception as e:
            print("ERROR:", e)
            messagebox.showerror("Error", str(e))

    Button(signup_page, text="Signup", command=signup).pack(pady=10)
    Button(login_page, text="Login", command=login).pack(pady=10)
