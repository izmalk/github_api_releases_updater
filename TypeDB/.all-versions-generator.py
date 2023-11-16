import requests

GITHUB_REPO = "vaticle/typedb"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
FILENAME_ALL = "all-versions.adoc"
FILENAME_LATEST = "latest-version.adoc"
ERRORS = []


def check_url(url):
    """Check if the URL exists and accessible (status code < 400)."""
    return requests.head(url).ok


def get_versions(url):
    """Fetch all versions from the GitHub API and process them."""
    result = []
    response = requests.get(f"{url}?per_page=100")
    releases = response.json()
    for release in releases:
        if "TypeDB" in release["name"]:
            print("Version " + release["tag_name"] + " will be processed.")
            result.append(get_release_data(release))
        else:
            print("Version " + release["tag_name"] + " IGNORED: no TypeDB in the name field.")
    return result


def get_release_data(release):
    """Process each release data and extract information."""
    data = {
        "version": release["tag_name"],
        "release_notes": release["html_url"],
        "assets": {
            "win": {
                "arm": {
                    "url": {},
                    "check": {}
                },
                "x86": {
                    "url": {},
                    "check": {}
                }
            },
            "lin": {
                "arm": {
                    "url": {},
                    "check": {}
                },
                "x86": {
                    "url": {},
                    "check": {}
                }
            },
            "mac": {
                "arm": {
                    "url": {},
                    "check": {}
                },
                "x86": {
                    "url": {},
                    "check": {}
                }
            }
        }
    }
    # todo rewrite with classes and objects
    for asset in release["assets"]:
        name = asset["name"].lower()
        key = "arm" if "arm64" in name else "x86" if "x86_64" in name else "x86"
        if "typedb-all-linux" in name:
            data["assets"]["lin"][key]["url"], data["assets"]["lin"][key]["check"] = get_asset_data(asset)
        elif "typedb-all-mac" in name:
            data["assets"]["mac"][key]["url"], data["assets"]["mac"][key]["check"] = get_asset_data(asset)
        elif "typedb-all-windows" in name:
            data["assets"]["win"][key]["url"], data["assets"]["win"][key]["check"] = get_asset_data(asset)
    return data


def get_asset_data(asset):
    """Extract data from asset and verify URL."""
    global ERRORS
    url = asset["browser_download_url"]
    if check_url(url):
        check = "PASSED"
    else:
        check = "Fail"
        ERRORS.append(url)
    return url, check


def generate_table_contents(versions, tags=False):
    """Generate the table contents in asciidoc syntax."""
    result = ""
    for version in versions:
        result += f"\n| {version['release_notes']}[{version['version']}]\n"
        for os_key in ["mac", "lin", "win"]:
            result += '| '
            if tags:
                result += f"\n// tag::{os_key}[]\n"
            assets = version["assets"][os_key]
            result += f"{assets['x86']['url']}[x86_64]"
            url_check_status = f"{assets['x86']['check']}"
            if assets["arm"]['url'] != {}:
                result += f" / {assets['arm']['url']}[arm64]"
                url_check_status += f" {assets['arm']['check']}"
            result += "\n"
            if tags:
                result += f"// end::{os_key}[]\n"
            result += f"// Check: {url_check_status}\n"
    return result


def write_file(file_name, content):
    """Write content to the specified file."""
    with open(file_name, "w") as file:
        file.write(content)


def print_json(url):
    x = requests.get(url + "?per_page=100")
    json_data = x.json()
    for json_element in json_data:
        print(json_element)


if __name__ == "__main__":
    """Main workflow"""
    versions = get_versions(API_URL)

    all_downloads = generate_table_contents(versions)
    try:
        write_file(FILENAME_ALL, all_downloads)
        print("\nFile", FILENAME_ALL, "write complete!")
    except IOError:
        print("Error while writing file:", FILENAME_ALL)

    latest_downloads = generate_table_contents([versions[0]], True)
    try:
        write_file(FILENAME_LATEST, latest_downloads)
        print("\nFile", FILENAME_LATEST, "write complete!")
    except IOError:
        print("Error while writing file:", FILENAME_LATEST)

    for error in ERRORS:
        print("Warning! The following error occurred:", error)
