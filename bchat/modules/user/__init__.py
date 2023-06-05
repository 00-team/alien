from .age import H_AGE_CONV
from .block import H_BLOCK
from .code import H_CODE_CONV
from .gender import H_GENDER_CONV
from .link import H_LINK
from .name import H_NAME_CONV
from .picture import H_PICTURE_CONV
from .profile import H_PROFILE
from .save import H_SAVE

HANDLERS_USER = [
    H_NAME_CONV,
    H_AGE_CONV,
    H_CODE_CONV,
    H_GENDER_CONV,
    H_PICTURE_CONV,
    *H_LINK,
    *H_PROFILE,
    *H_SAVE,
    *H_BLOCK,
]
