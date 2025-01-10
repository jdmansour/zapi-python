"""Cleans up an OpenAPI specification to be used with openapi-python-client."""

import argparse
import json
import sys

import requests


def main():
    parser = argparse.ArgumentParser(
        description="Cleans up an OpenAPI specification to be used with openapi-python-client."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--path", help="Path to the OpenAPI specification file.")
    group.add_argument("--url", help="URL to the OpenAPI specification file.")
    args = parser.parse_args()

    if args.url:
        response = requests.get(args.url, timeout=5)
        response.raise_for_status()
        obj = response.json()
    else:
        with open(args.path, encoding="utf-8") as f:
            obj = json.load(f)

    print("Searching for duplicate titles...", file=sys.stderr)

    # Find all the schemas
    paths = []
    collect_from_components(obj, paths)
    collect_from_paths(obj, paths)
    # print("Found schemas:", paths, file=sys.stderr)

    # Find the ones that have duplicate titles
    dupl_lists = find_duplicates_by_title(obj, paths)

    # remove the title from all duplicates
    count = sum(len(d) for d in dupl_lists.values())
    print(f"Removing {count} duplicate titles.", file=sys.stderr)
    for dups in dupl_lists.values():
        for d in dups:
            schema = find_path(obj, d)

            if "title" in schema:
                # print(f"Removing title from {schema['title']}", file=sys.stderr)
                del schema["title"]

    json.dump(obj, sys.stdout, indent=2)
    print("Done.", file=sys.stderr)


def collect_from_paths(obj: dict, output):
    """Gets all the inline schemas from 'paths'."""
    paths = obj["paths"]
    for k, p in paths.items():
        # print('k', k, file=sys.stderr)
        for method, methodinfo in p.items():
            # print("methodinfo.keys", methodinfo.keys(), file=sys.stderr)
            for code, response in methodinfo.get("responses", {}).items():
                # print('code', code, file=sys.stderr)
                for mime, definition in response.get("content", {}).items():
                    if "schema" in definition:
                        # mime = mime.replace('/', '%2F')
                        parts = ("paths", k, method, "responses",
                                 code, "content", mime, "schema")
                        path = "/".join(p.replace("/", "%2F") for p in parts)
                        handle_schema(path, definition["schema"], output)


def collect_from_components(obj, output):
    """Gets all the schemas from 'components/schemas'."""
    schemas = obj["components"]["schemas"]
    for s in schemas:
        handle_schema("components/schemas/" + s, schemas[s], output)


def handle_schema(path: str, s: dict, output):
    """Adds a schema and all sub-schemas to output."""

    # print("handle_schema %r %r" % (path, s), file=sys.stderr)
    if s.get("type", None) == "object":
        output.append(path)

        for pk, pv in s.get("properties", {}).items():
            handle_schema(path + "/properties/" + pk, pv, output)
        # for pk, pv in s.get('additionalProperties', {}).get('items', {}).items():
        #     print("calling handle_schema with %r %r" % (path + '/' + pk, pv), file=sys.stderr)
        #     handle_schema(path + '/' + pk, pv, output)
    elif s.get("type", None) == "array":
        # output.append(path)

        handle_schema(path + "/items", s["items"], output)


def find_duplicates_by_title(obj, paths):
    """Returns groups of schemas with the same title.
    obj is the OpenAPI JSON object, paths a list of JSON paths to schemas.

    Returns a dict of the form
    { 'path/to/schema': ['path/to/schema', 'path/to/other/schema'] }
    """
    seen = {}
    # one name -> list of names
    dupl_lists = {}

    def criterion(key, data):
        title = data.get("title", None)
        if title:
            return title
        # return key
        return None

    for k1 in paths:
        # print("considering path", k1, file=sys.stderr)
        v1 = find_path(obj, k1)
        crit1 = criterion(k1, v1)
        if crit1 is None:
            continue

        for k2, v2 in seen.items():
            crit2 = criterion(k2, v2)
            if crit2 is None:
                continue
            if crit1 == crit2:
                if k2 not in dupl_lists:
                    dupl_lists[k2] = [k2]
                dupl_lists[k2].append(k1)
                break
        else:  # when not breaked
            seen[k1] = v1

    return dupl_lists


def find_path(obj, path):
    """Finds a node in JSON by path, separated by slashes."""

    parts = [p.replace("%2F", "/") for p in path.split("/")]
    value = obj
    for p in parts:
        value = value[p]
    return value


if __name__ == "__main__":
    main()
