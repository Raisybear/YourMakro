from app.utils.auth import (
    hash_password,
    is_valid_email,
    create_user,
    verify_credentials
)

from app.utils.mouse import (
    on_click,
    get_positions,
    start_adding_positions,
    start_clicking,
    save_positions,
    load_positions,
    get_user_sets,
    delete_set,
    positions
)

from app.utils.ui import (
    create_drag_icon,
    DragManager,
    show_message,
    confirm_dialog,
    format_datetime,
    configure_treeview_style
)

# Make the imported functions and variables available at the module level
__all__ = [
    # Auth utilities
    'hash_password',
    'is_valid_email',
    'create_user',
    'verify_credentials',

    # Mouse utilities
    'on_click',
    'get_positions',
    'start_adding_positions',
    'start_clicking',
    'save_positions',
    'load_positions',
    'get_user_sets',
    'delete_set',
    'positions',

    # UI utilities
    'create_drag_icon',
    'DragManager',
    'show_message',
    'confirm_dialog',
    'format_datetime',
    'configure_treeview_style'
]