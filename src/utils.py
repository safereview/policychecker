def read_file(fpath):
    with open(fpath, encoding="utf-8") as f:
        return f.read()


def encode_dict(data):
	return {str(key):str(value) for key,value in data.items()}
