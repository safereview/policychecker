# GitHub
GITHUB = 'github'
GITHUB_API = "https://api.github.com/repos"
GITHUB_REQURIED_REVIEWS = 'required_pull_request_reviews'
GITHUB_MIN_APPROALS = 'required_approving_review_count'
GITHUB_CODE_OWNER_REVIEWS = 'require_code_owner_reviews'
GITHUB_DISMISS_STALE_REVIEWS = 'dismiss_stale_reviews'
GITHUB_DISMISSAL_RESTRICTION = 'dismissal_restrictions'
GITHUB_AUTHORIZED_DISMISS = 'allowed_to_dismis_reviews'
GITHUB_ENFORCE_ADMIN = 'enforce_admins'
GITHUB_PUSH_RESTRICTIONS = 'restrictions'
GITHUB_AUTHORIZED_PUSH = 'allowed_to_push'
GITHUB_LINEAR_HISTORY = 'required_linear_history'
GITHUB_REQURIED_SIGNED_COMMIT = 'required_signed_commits'
CODEOWNERS_LOCATIONS = ['.github/CODEOWNERS', 'CODEOWNERS', 'docs/CODEOWNERS']
CODEOWNERS = "CODEOWNERS"
GITATTRIBUTES = ".gitattributes"
PROTECTION_RULES = "ProtectionRules"
COLLABORATORS = 'collaborators'

# Gerrit
GERRIT = 'gerrit'
CONFIG_BRANCH = 'refs/meta/config'
CONFIG_PROJECT = 'project.config'
CONFIG_GROUPS = 'groups'
CONFIG_RULES = 'rules.pl'
CONFIG_GROUPS_MEMBERS = 'GroupsMembers'
ALL_PROJECTS = 'All-Projects'

# Merge Options
#MERGE_METHOD = 'merge_method'
MERGE = 'Merge'
REBASE = 'Rebase'
SQUASH = 'SquashAndMerge'
FIRSTCOMMIT = 'FirstCommit'
DIRECTPUSH = 'DirectPush'

# PGP
PGP_SIG = 'gpgsig'
PGP_START = '-----BEGIN PGP SIGNATURE-----'
PGP_END = '-----END PGP SIGNATURE-----'

# Crypto
# TODO: Make it work for any condition in particular
# when there is no existing keys at ~/.gnupg/ or 'C:\\Users\\user\\.gnupg'
# KEYS_DIR = '/home/hmd/.gnupg'
KEYS_DIR = '/home/fernando/.gnupg'
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
