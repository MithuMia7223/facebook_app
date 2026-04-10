from tkinter import *
from tkinter import ttk, Text
from auth import build_auth
import auth
import profile
import posts
import friends
import ws
import json
import threading

main = Tk()
main.title("Social App")
main.geometry("900x650")


fb = ttk.Notebook(main)
fb.pack(fill="both", expand=True)

login_page = ttk.Frame(fb)
signup_page = ttk.Frame(fb)
profile_page = ttk.Frame(fb)
posts_page = ttk.Frame(fb)
friends_page = ttk.Frame(fb)


fb.add(login_page, text="Login")
fb.add(signup_page, text="Signup")


profile_text = Text(profile_page, height=10)
profile_text.pack(fill="both", expand=True)


new_post_entry = Entry(posts_page, width=50)
new_post_entry.pack(pady=10)

posts_table = ttk.Treeview(
    posts_page, columns=("Content", "Likes", "Comment"), show="headings"
)
posts_table.heading("Content", text="Content")
posts_table.heading("Likes", text="Likes")
posts_table.heading("Comment", text="Comment")
posts_table.pack(fill="both", expand=True)

friends_table = ttk.Treeview(friends_page, columns=("ID", "Username"), show="headings")
friends_table.heading("ID", text="ID")
friends_table.heading("Username", text="Username")
friends_table.pack(fill="both", expand=True)

friend_entry = Entry(friends_page)
friend_entry.pack(pady=5)

auth.build_auth(
    fb,
    login_page,
    signup_page,
    profile_page,
    posts_page,
    friends_page,
    main,
    profile_text,
    None,
    None,
    None,
)

profile.build_profile(
    profile_page, profile_text, fb, login_page, signup_page, posts_page, friends_page
)
posts.build_posts(posts_page, posts_table, new_post_entry)
friends.build_friends(friends_page, friends_table, friend_entry)

threading.Thread(target=ws.start_listening, daemon=True).start()


def poll_messages():
    try:
        message = ws.messages.get_nowait()
    except:
        main.after(100, poll_messages)
        return

    try:
        print("Polling message: ", message)
        payload = json.loads(message)

        if payload.get("event") == "post:new":
            posts.messages.put(message)
            pass

    except:
        print("Could not parse message: " + message)

    main.after(100, poll_messages)


poll_messages()
main.mainloop()
