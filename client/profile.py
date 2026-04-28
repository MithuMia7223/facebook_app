from tkinter import Button, Entry, Label, messagebox, Frame, filedialog
from PIL import Image, ImageTk
import requests
import config


def _auth_tuple():
    user = getattr(config, "signed_in_username", "")
    pwd = getattr(config, "signed_in_password", "")
    if not user or not pwd:
        return None
    return (user, pwd)


def build_profile(
    profile_page, profile_text, fb, login_page, signup_page, posts_page, friends_page
):

    frame = Frame(profile_page)
    frame.pack(pady=10)

    avatar_label = Label(frame, text="No Avatar")
    avatar_label.pack(pady=5)

    cover_label = Label(profile_page, text="No Cover Photo")
    cover_label.pack(pady=5)

    name_entry = Entry(profile_page, width=40)
    bio_entry = Entry(profile_page, width=60)
    location_entry = Entry(profile_page, width=40)
    phone_entry = Entry(profile_page, width=40)

    Label(profile_page, text="Name").pack()
    name_entry.pack()

    Label(profile_page, text="Bio").pack()
    bio_entry.pack()

    Label(profile_page, text="Location").pack()
    location_entry.pack()

    Label(profile_page, text="Phone").pack()
    phone_entry.pack()

    stats_label = Label(profile_page, text="")
    stats_label.pack(pady=10)

    
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
            config.signed_in_user_id = data.get("id")

            profile_text.delete("1.0", "end")
            profile_text.insert(
                "end",
                f"ID: {data.get('id')}\n"
                f"Username: {data.get('username')}\n"
                f"Name: {data.get('name')}\n"
                f"Bio: {data.get('bio')}\n"
            )

            # fill fields
            name_entry.delete(0, "end")
            name_entry.insert(0, data.get("name", ""))

            bio_entry.delete(0, "end")
            bio_entry.insert(0, data.get("bio", ""))

            location_entry.delete(0, "end")
            location_entry.insert(0, data.get("location", ""))

            phone_entry.delete(0, "end")
            phone_entry.insert(0, data.get("phone", ""))

            # stats
            stats_label.config(
                text=f"Posts: {data.get('post_count', 0)} | "
                     f"Comments: {data.get('comment_count', 0)} | "
                     f"Friends: {len(data.get('friends', []))}"
            )

            
            avatar_url = data.get("avatar_url")
            if avatar_url:
                try:
                    img_data = requests.get(config.API_BASE_URL + avatar_url, stream=True).raw
                    img = Image.open(img_data).resize((100, 100))
                    img = ImageTk.PhotoImage(img)

                    avatar_label.config(image=img, text="")
                    avatar_label.image = img
                except:
                    avatar_label.config(text="Image Error")
            else:
                avatar_label.config(text="No Avatar")

            
            cover_url = data.get("cover_photo")
            if cover_url:
                try:
                    img_data = requests.get(config.API_BASE_URL + cover_url, stream=True).raw
                    img = Image.open(img_data).resize((400, 120))
                    img = ImageTk.PhotoImage(img)

                    cover_label.config(image=img, text="")
                    cover_label.image = img
                except:
                    cover_label.config(text="Cover Error")
            else:
                cover_label.config(text="No Cover Photo")

        except Exception as e:
            messagebox.showerror("Profile", str(e))

    
    def update_profile():
        auth = _auth_tuple()
        user_id = getattr(config, "signed_in_user_id", None)

        if not auth:
            messagebox.showwarning("Profile", "Login first")
            return

        payload = {
            "name": name_entry.get(),
            "bio": bio_entry.get(),
            "location": location_entry.get(),
            "phone": phone_entry.get(),
        }

        try:
            r = requests.patch(
                f"{config.API_BASE_URL}/users/me/update",
                json=payload,
                auth=auth,
            )

            if r.status_code not in [200, 201, 204]:
                messagebox.showerror("Profile", r.text)
                return

            messagebox.showinfo("Profile", "Updated successfully")
            load_profile()

        except Exception as e:
            messagebox.showerror("Profile", str(e))

    
    def upload_avatar():
        auth = _auth_tuple()
        if not auth:
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "rb") as f:
                r = requests.post(
                    f"{config.API_BASE_URL}/users/me/avatar",
                    files={"file": f},
                    auth=auth,
                )

            if r.status_code in [200, 201]:
                messagebox.showinfo("Profile", "Avatar uploaded")
                load_profile()
            else:
                messagebox.showerror("Profile", r.text)

        except Exception as e:
            messagebox.showerror("Profile", str(e))

    
    def upload_cover():
        auth = _auth_tuple()
        if not auth:
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "rb") as f:
                r = requests.post(
                    f"{config.API_BASE_URL}/users/me/cover",
                    files={"file": f},
                    auth=auth,
                )

            if r.status_code == 200:
                messagebox.showinfo("Profile", "Cover updated")
                load_profile()
            else:
                messagebox.showerror("Profile", r.text)

        except Exception as e:
            messagebox.showerror("Profile", str(e))

    
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

        messagebox.showinfo("Logout", "Logged out")

    
    Button(profile_page, text="Upload Avatar", command=upload_avatar).pack(pady=4)
    Button(profile_page, text="Upload Cover", command=upload_cover).pack(pady=4)
    Button(profile_page, text="Load Profile", command=load_profile).pack(pady=4)
    Button(profile_page, text="Update Profile", command=update_profile).pack(pady=4)
    Button(profile_page, text="Logout", command=logout).pack(pady=10)

    return load_profile