from tkinter import Button, Frame, Label, messagebox, ttk
import requests

import config


def _auth_tuple():
    user = getattr(config, "signed_in_username", "")
    pwd = getattr(config, "signed_in_password", "")
    if not user or not pwd:
        return None
    return (user, pwd)


def _current_user_id(auth):
    # Use cached user id if available; otherwise fetch once from /users/me.
    user_id = getattr(config, "signed_in_user_id", None)
    if user_id:
        return user_id

    me = requests.get(f"{config.API_BASE_URL}/users/me", auth=auth)
    if me.status_code == 200:
        user_id = me.json().get("id")
        config.signed_in_user_id = user_id
        return user_id

    return None


def build_friends(friends_page, friends_table, friend_entry):
    requests_table = None

    def clear_friends_table():
        for item in friends_table.get_children():
            friends_table.delete(item)

    def clear_requests_table():
        for item in requests_table.get_children():
            requests_table.delete(item)

    def load_friends():
        auth = _auth_tuple()
        if not auth:
            messagebox.showwarning("Friends", "Please login first")
            return

        try:
            user_id = _current_user_id(auth)
            if not user_id:
                messagebox.showerror("Friends", "User ID not found")
                return

            r = requests.get(f"{config.API_BASE_URL}/users/{user_id}/friends")
            if r.status_code != 200:
                messagebox.showerror("Friends", r.text)
                return

            clear_friends_table()
            data = r.json().get("data", [])
            for friend in data:
                friends_table.insert(
                    "",
                    "end",
                    iid=str(friend.get("id")),
                    values=(friend.get("id"), friend.get("username", "")),
                )

        except Exception as e:
            messagebox.showerror("Friends", str(e))

    def send_friend_request():
        auth = _auth_tuple()
        if not auth:
            messagebox.showwarning("Friends", "Please login first")
            return

        # Accept either numeric friend id or username from input box.
        raw_value = friend_entry.get().strip()
        if not raw_value:
            messagebox.showwarning("Friends", "Enter friend ID or username")
            return

        try:
            user_id = _current_user_id(auth)
            if not user_id:
                messagebox.showerror("Friends", "User ID not found")
                return

            friend_id = None
            if raw_value.isdigit():
                friend_id = int(raw_value)
            else:
                # If user typed username, resolve it to id first.
                lookup = requests.get(
                    f"{config.API_BASE_URL}/users/username/{raw_value}"
                )
                if lookup.status_code == 200:
                    friend_id = lookup.json().get("id")

            if not friend_id:
                messagebox.showerror("Friends", "Friend not found")
                return

            r = requests.post(
                f"{config.API_BASE_URL}/users/{user_id}/friend-requests/{friend_id}",
                auth=auth,
            )
            if r.status_code not in [200, 201]:
                messagebox.showerror("Friends", r.text)
                return

            messagebox.showinfo("Friends", "Friend request sent")
            friend_entry.delete(0, "end")
            load_incoming_requests()

        except Exception as e:
            messagebox.showerror("Friends", str(e))

    def load_incoming_requests():
        auth = _auth_tuple()
        if not auth:
            messagebox.showwarning("Friends", "Please login first")
            return

        try:
            user_id = _current_user_id(auth)
            if not user_id:
                messagebox.showerror("Friends", "User ID not found")
                return

            r = requests.get(
                f"{config.API_BASE_URL}/users/{user_id}/friend-requests/incoming",
                auth=auth,
            )
            if r.status_code != 200:
                messagebox.showerror("Friends", r.text)
                return

            clear_requests_table()
            data = r.json().get("data", [])
            for req in data:
                request_id = str(req.get("request_id"))
                sender_id = req.get("sender_id")
                sender_username = req.get("sender_username", "")
                requests_table.insert(
                    "",
                    "end",
                    iid=request_id,
                    values=(request_id, sender_id, sender_username),
                )
        except Exception as e:
            messagebox.showerror("Friends", str(e))

    def accept_selected_request():
        auth = _auth_tuple()
        if not auth:
            messagebox.showwarning("Friends", "Please login first")
            return

        selected = requests_table.selection()
        if not selected:
            messagebox.showwarning("Friends", "Select a request first")
            return

        request_id = selected[0]
        try:
            user_id = _current_user_id(auth)
            if not user_id:
                messagebox.showerror("Friends", "User ID not found")
                return

            r = requests.post(
                f"{config.API_BASE_URL}/users/{user_id}/friend-requests/{request_id}/accept",
                auth=auth,
            )
            if r.status_code != 200:
                messagebox.showerror("Friends", r.text)
                return

            load_incoming_requests()
            load_friends()
        except Exception as e:
            messagebox.showerror("Friends", str(e))

    def reject_selected_request():
        auth = _auth_tuple()
        if not auth:
            messagebox.showwarning("Friends", "Please login first")
            return

        selected = requests_table.selection()
        if not selected:
            messagebox.showwarning("Friends", "Select a request first")
            return

        request_id = selected[0]
        try:
            user_id = _current_user_id(auth)
            if not user_id:
                messagebox.showerror("Friends", "User ID not found")
                return

            r = requests.delete(
                f"{config.API_BASE_URL}/users/{user_id}/friend-requests/{request_id}",
                auth=auth,
            )
            if r.status_code != 200:
                messagebox.showerror("Friends", r.text)
                return

            load_incoming_requests()
        except Exception as e:
            messagebox.showerror("Friends", str(e))

    def remove_selected_friend():
        auth = _auth_tuple()
        if not auth:
            messagebox.showwarning("Friends", "Please login first")
            return

        selected = friends_table.selection()
        if not selected:
            messagebox.showwarning("Friends", "Select a friend first")
            return

        friend_id = selected[0]

        try:
            user_id = _current_user_id(auth)
            if not user_id:
                messagebox.showerror("Friends", "User ID not found")
                return

            r = requests.delete(
                f"{config.API_BASE_URL}/users/{user_id}/friends/{friend_id}",
                auth=auth,
            )
            if r.status_code != 200:
                messagebox.showerror("Friends", r.text)
                return

            load_friends()

        except Exception as e:
            messagebox.showerror("Friends", str(e))

    actions = Frame(friends_page)
    actions.pack(pady=5)

    Button(actions, text="Send Request", command=send_friend_request).pack(
        side="left", padx=5
    )
    Button(actions, text="Refresh", command=load_friends).pack(side="left", padx=5)
    Button(actions, text="Remove Selected", command=remove_selected_friend).pack(
        side="left", padx=5
    )

    Label(friends_page, text="Incoming Friend Requests").pack(pady=6)
    requests_table = ttk.Treeview(
        friends_page,
        columns=("Request ID", "From ID", "Username"),
        show="headings",
        height=6,
    )
    requests_table.heading("Request ID", text="Request ID")
    requests_table.heading("From ID", text="From ID")
    requests_table.heading("Username", text="Username")
    requests_table.pack(fill="both", expand=True, pady=4)

    request_actions = Frame(friends_page)
    request_actions.pack(pady=5)
    Button(
        request_actions, text="Load Requests", command=load_incoming_requests
    ).pack(side="left", padx=5)
    Button(
        request_actions, text="Accept Request", command=accept_selected_request
    ).pack(side="left", padx=5)
    Button(
        request_actions, text="Reject Request", command=reject_selected_request
    ).pack(side="left", padx=5)
