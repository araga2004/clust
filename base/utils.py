import diff_match_patch as dmp_module

dmp = dmp_module.diff_match_patch()

def get_diff(old, new):
    patches = dmp.patch_make(old, new)
    return dmp.patch_toText(patches)

def apply_diff(old, diff_text):
    patches = dmp.patch_fromText(diff_text)
    new_text, _ = dmp.patch_apply(patches, old)
    return new_text

def reconstruct_code(room, upto_version=None):
    if upto_version is None:
        upto_version = room.snippets.latest('version_number').version_number

    full_snapshot = (
        room.snippets
        .filter(is_full=True, version_number__lte=upto_version)
        .order_by('-version_number')
        .first()
    )

    if not full_snapshot:
        return ""

    code = full_snapshot.code_diff

    diffs = (
        room.snippets
        .filter(version_number__gt=full_snapshot.version_number, version_number__lte=upto_version)
        .order_by('version_number')
    )

    for version in diffs:
        code = apply_diff(code, version.code_diff)

    return code
