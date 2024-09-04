from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group , Permission
from django.contrib.auth.decorators import login_required, permission_required
from .forms import UserForm, GroupForm

# User Management Views
@login_required
@permission_required('auth.view_user', raise_exception=True)
def user_list(request):
    users = User.objects.all()
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
@permission_required('auth.add_user', raise_exception=True)
def user_create(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            return redirect('user_list')
    else:
        form = UserForm()
    return render(request, 'accounts/user_form.html', {'form': form})

@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password1']:
                user.set_password(form.cleaned_data['password1'])
            user.save()
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form})

@login_required
@permission_required('auth.delete_user', raise_exception=True)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})

# Group Management Views
@login_required
@permission_required('auth.view_group', raise_exception=True)
def group_list(request):
    groups = Group.objects.all()
    return render(request, 'accounts/group_list.html', {'groups': groups})

@login_required
@permission_required('auth.add_group', raise_exception=True)
def group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('group_list')
    else:
        form = GroupForm()
    return render(request, 'accounts/group_form.html', {'form': form})

@login_required
@permission_required('auth.change_group', raise_exception=True)
def group_update(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect('group_list')
    else:
        form = GroupForm(instance=group)
    return render(request, 'accounts/group_form.html', {'form': form})

@login_required
@permission_required('auth.delete_group', raise_exception=True)
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.delete()
        return redirect('group_list')
    return render(request, 'accounts/group_confirm_delete.html', {'group': group})


@login_required
@permission_required('auth.view_permission', raise_exception=True)
def rights_management(request):
    permissions = Permission.objects.all()
    return render(request, 'accounts/rights_management.html', {'permissions': permissions})