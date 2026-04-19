def can_access_board(board, user):
    if user.is_staff:
        return True
    return board.created_by_id == user.id or board.members.filter(user=user).exists()


def is_board_owner(board, user):
    if user.is_staff:
        return True
    return board.created_by_id == user.id
