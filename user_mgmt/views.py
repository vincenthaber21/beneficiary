from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from utils import admin_required
from .models import UserProfile
from .forms import UserCreateForm, UserEditForm


@admin_required
def user_list(request):
    users = User.objects.select_related("profile").order_by("username")
    return render(request, "user_mgmt/list.html", {"users": users})


@admin_required
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        user = User.objects.create_user(
            username=d["username"],
            password=d["password"],
            first_name=d.get("first_name", ""),
            last_name=d.get("last_name", ""),
            email=d.get("email", ""),
        )
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = d["role"]
        profile.save()
        messages.success(request, f'User "{user.username}" created successfully.')
        return redirect("user_mgmt:list")
    return render(request, "user_mgmt/form.html", {"form": form, "action": "Add"})


@admin_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    initial = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": profile.role,
        "is_active": user.is_active,
    }
    form = UserEditForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        user.first_name = d["first_name"]
        user.last_name = d["last_name"]
        user.email = d["email"]
        user.is_active = d.get("is_active", True)
        if d.get("password"):
            user.set_password(d["password"])
        user.save()
        profile.role = d["role"]
        profile.save()
        messages.success(request, f'User "{user.username}" updated.')
        return redirect("user_mgmt:list")
    return render(request, "user_mgmt/form.html", {"form": form, "action": "Edit", "target_user": user})


@admin_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect("user_mgmt:list")
    if request.method == "POST":
        user.delete()
        messages.success(request, "User deleted.")
        return redirect("user_mgmt:list")
    return render(request, "user_mgmt/confirm_delete.html", {"target_user": user})
