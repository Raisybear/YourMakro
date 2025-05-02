# This file makes the controllers directory a Python package
# Import controllers for easier access

from app.controllers.auth_controller import (
    hash_password,
    is_valid_email,
    create_user,
    verify_credentials,
    get_all_users
)

from app.controllers.position_controller import (
    save_positions,
    load_positions,
    get_user_sets,
    delete_set,
    copy_set,
    create_empty_set,
    on_click,
    get_positions,
    start_adding_positions,
    start_clicking,
    set_click_speed
)

from app.controllers.user_controller import (
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    update_last_login,
    update_user_profile,
    get_user_statistics,
    delete_user_account
)

# Global variables accessible via the controllers package
from app.controllers.position_controller import positions, adding_positions, click_speed