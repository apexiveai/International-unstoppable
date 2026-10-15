from fastapi import Depends, HTTPException, status

from app.auth import get_current_user


def require_authenticated_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled.",
        )
    return current_user


def require_admin(current_user=Depends(require_authenticated_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )
    return current_user


def require_super_admin(current_user=Depends(require_authenticated_user)):
    if not current_user.is_admin or not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super administrator access required.",
        )
    return current_user


def require_subscription_operator(current_user=Depends(require_admin)):
    if current_user.role.strip().upper() == "SUPPORT" and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription changes require Admin access.",
        )
    return current_user
