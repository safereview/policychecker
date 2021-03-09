# GitHub
CODEOWNERS = ".github/CODEOWNERS"
GITATTRIBUTES = ".gitattributes"
PROTECTION_RULES = "ProtectionRules"
GITHUB_API = "https://api.github.com/repos"
GITHUB = 'github'

GITHUB_REQURIED_REVIEWS = 'required_pull_request_reviews'
GITHUB_MIN_APPROALS = 'required_approving_review_count'
GITHUB_DISMISS_STALE_REVIEWS = 'dismiss_stale_reviews'
GITHUB_CODE_OWNER_REVIEWS = 'require_code_owner_reviews'
GITHUB_ENFORCE_ADMIN = 'enforce_admins'


# Gerrit
CONFIG_BRANCH = 'refs/meta/config'
CONFIG_PROJECT = 'project.config'
CONFIG_GROUPS = 'groups'
CONFIG_RULES = 'rules.pl'
ALL_PROJECTS = 'All-Projects'
GERRIT = 'gerrit'

# Git
FIRSTCOMMIT = 'FirstCommit'
DIRECTPUSH = 'DirectPush'
MERGE = 'Merge'
REBASE = 'Rebase'
SQUASH = 'SquashAndMerge'
PGP_SIG = 'gpgsig'
PGP_START = '-----BEGIN PGP SIGNATURE-----'
PGP_END = '-----END PGP SIGNATURE-----'

# TODO: Make it work for any condition in particular
# when there is no existing keys at ~/.gnupg/
#'C:\\Users\\hye\\.gnupg'
KEYS_DIR = '/home/hmd/.gnupg'
ED25519_KEY = 'ed25519_pub_key.pem'

# Gerrit Rules
GERRIT_LABELS = {
    #ANY_WITH_BLOCK
    "ANYWITHBLOCK": {
        "isBlock": True,
        "isRequired": False,
        "requiresMaxValue": False
    },
    #MAX_NO_BLOCK
    "MAXNOBLOCK": {
        "isBlock": False,
        "isRequired": True,
        "requiresMaxValue": True
    },
    #MAX_WITH_BLOCK
    "MAXWITHBLOCK": {
        "isBlock": True,
        "isRequired": True,
        "requiresMaxValue": True
    },
    #NO_BLOCK
    "NOBLOCK": {
    },
    "NoOp": {
    },
    "PatchSetLock": {
    }
}
