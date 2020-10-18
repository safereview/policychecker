# Replace all "/" occurrences with "%2F"
def file_path_trim(fpath):
    return fpath.replace('/', '%2F')

# Read a local file
def read_file(fpath):
    with open(fpath, encoding="utf-8") as f:
        return f.read()

# Encode a dictionary
def encode_dict(data):
	return {str(key):str(value) for key,value in data.items()}