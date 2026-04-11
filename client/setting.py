from tkinter import *
from tkinter import messagebox
import requests
import config

def _auth_tuple():
    user = getattr(config, "signed_in_username", "")
    pwd = getattr(config, "signed_in_password", " ")

    if not user or not pwd:
        return None
    return (user, pwd)

def open_setting(main_window):

    win = Toplevel(main_window)
    win.title("Settings")
    win.geometry("350x350")

    Label(win, text= "Settings", font=("Arial", 14, "bold")).pack(pady=10)

    def logout():
        config.signed_in_username = None
        config.signed_in_password = None
        config.signed_in_user_id = None

        messagebox.showerror("Logout", width=25, command=logout).pack(pady=5)

    Button(win, text="Logout", width=25, command=logout).pack(pady=5)

    def delete_account():
        auth = _auth_tuple()
        user_id = getattr(config, "signed_in_user_id", None)

        if not auth or not user_id:
            messagebox.showwarning("Delete", "Please login first")
            return
        
        confirm = messagebox.askyesno(
            "Delete Account",
            "Are you sure? This action cannot be undone!"
        )
        if not confirm:
            return
        
        try:
            r = requests.delete(
                f"{config.API_BASE_URL}/users/{user_id}",
                auth=auth
            )
            
            if r.status_code == 200:
                messagebox.showerror("Delete", "Accoutn delete successfully")
                logout()
            else:
                messagebox.showerror("Delete", r.text)
        except Exception as e:
            messagebox.showerror("Delete", str(e))

    Button(win, text="Delete Accoutn", width=25, command=delete_account).pack(pady=5)

    def deactive_account():
        auth = _auth_tuple()
        user_id = getattr(config, "signed_in_user_id", None)

        if not auth or not user_id:
            messagebox.showerror("Deactivate", "Please loing first")
            return
        
        try:
            r = requests.patch(
                f"{config.API_BASE_URL}/users/{user_id}",
                json={"active": False},
                auth=auth
            )
            if r.status_code == 200:
                messagebox.showinfo("Deactivate", "Account deactivated")
                logout()
            else:
                messagebox.showerror("Deactivate", r.text)

        except Exception as e:
            messagebox.showerror("Deactivate", str(e))
    Button(win, text="Deactivate Account", width=25, command=deactive_account).pack(pady=5)
        
    def refresh_profile():
        auth = _auth_tuple()
        if not auth:
            messagebox.showwarning("Profile", "Please login first")
            return
        try:
            r = requests.get(f"{config.API_BASE_URL}/users/me", auth=auth)

            if r.status_code == 200:
                data = r.json()
                config.signed_in_user_id = data.get("id")
                messagebox.showinfo("Profile", "Profile refreshed")
            else:
                messagebox.showerror("Profile", r.text)

        except Exception as e:
            messagebox.showerror("Profile", str(e))
    Button(win, text="Refresh profile", width=25, command=refresh_profile).pack(pady=5)
    

