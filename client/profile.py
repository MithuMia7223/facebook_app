from tkinter import Button, Entry, Label, messagebox
import requests

import config


def _auth_tuple():
    # Helper: return (username, password) for authenticated requests.
    user = getattr(config, "signed_in_username", "")
    pwd = getattr(config, "signed_in_password", "")
    if not user or not pwd:
        return None
    return (user, pwd)


def build_profile(
    profile_page, profile_text, fb, login_page, signup_page, posts_page, friends_page
):
    name_entry = Entry(profile_page, width=40)
    bio_entry = Entry(profile_page, width=60)

    Label(profile_page, text="Name").pack(pady=3)
    name_entry.pack(pady=3)

    Label(profile_page, text="Bio").pack(pady=3)
    bio_entry.pack(pady=3)

    def logout():
        config.signed_in_username = None
        config.signed_in_password = None
        config.signed_in_user_id = None
        fb.forget(profile_page)
        fb.forget(posts_page)
        fb.forget(friends_page)
        fb.add(login_page, text="Login")
        fb.add(signup_page, text="Signup")
        fb.select(login_page)
        messagebox.showinfo("Logout", "Logged out successfully")

    Button(profile_page, text="Logout", command=logout).pack(pady=10)

    def load_profile():
        auth = _auth_tuple()
        if not auth:
            messagebox.showwarning("Profile", "Please login first")
            return

        try:
            r = requests.get(f"{config.API_BASE_URL}/users/me", auth=auth)
            if r.status_code != 200:
                messagebox.showerror("Profile", r.text)
                return

            data = r.json()
            # Cache user id for later update/friends API calls.
            config.signed_in_user_id = data.get("id")

            profile_text.delete("1.0", "end")
            profile_text.insert(
                "end",
                f"ID: {data.get('id')}\n"
                f"Username: {data.get('username', '')}\n"
                f"Name: {data.get('name', '')}\n"
                f"Bio: {data.get('bio', '')}\n",
            )

            name_entry.delete(0, "end")
            name_entry.insert(0, data.get("name", "") or "")

            bio_entry.delete(0, "end")
            bio_entry.insert(0, data.get("bio", "") or "")

        except Exception as e:
            messagebox.showerror("Profile", str(e))

    def update_profile():
        auth = _auth_tuple()
        user_id = getattr(config, "signed_in_user_id", None)

        if not auth:
            messagebox.showwarning("Profile", "Please login first")
            return

        if not user_id:
            try:
                me = requests.get(f"{config.API_BASE_URL}/users/me", auth=auth)
                if me.status_code == 200:
                    user_id = me.json().get("id")
                    config.signed_in_user_id = user_id
            except Exception:
                pass

        if not user_id:
            messagebox.showerror("Profile", "User ID not found")
            return

        # Send edited fields to PATCH /users/{id}.
        payload = {"name": name_entry.get(), "bio": bio_entry.get()}

        try:
            r = requests.patch(
                f"{config.API_BASE_URL}/users/{user_id}",
                json=payload,
                auth=auth,
            )
            if r.status_code != 200:
                messagebox.showerror("Profile", r.text)
                return

            messagebox.showinfo("Profile", "Updated successfully")
            load_profile()

        except Exception as e:
            messagebox.showerror("Profile", str(e))

    Button(profile_page, text="Load Profile", command=load_profile).pack(pady=4)
    Button(profile_page, text="Update Profile", command=update_profile).pack(pady=4)
