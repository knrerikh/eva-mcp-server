"""Response shapes and identifiers used across the Eva MCP test suite.

The response shapes below mirror what a live Eva instance returns, verified
against API v1.9.22 on 2026-09-05. The values are fictional on purpose: this
repository is public and must carry no real task codes, project codes, logins
or identifiers.

The *shape* matters as much as the values. Eva returns a relation as a nested
object carrying its own identifier, never as a plain string, and it addresses
every entity by an internal id of the form ``CmfTask:<uuid>``. A fixture that
flattens a relation to a string describes an API that does not exist, and a
suite built on it cannot fail on a defect in how relations are read or filtered
— which is exactly how a set of such defects once passed this suite green.
"""

# --- Identifiers -------------------------------------------------------------

TASK_ID = "CmfTask:11111111-1111-1111-1111-111111111111"
PROJECT_ID = "CmfProject:22222222-2222-2222-2222-222222222222"
PERSON_ID = "CmfPerson:33333333-3333-3333-3333-333333333333"
DOCUMENT_ID = "CmfDocument:44444444-4444-4444-4444-444444444444"
LIST_ID = "CmfList:55555555-5555-5555-5555-555555555555"
COMMENT_ID = "CmfComment:66666666-6666-6666-6666-666666666666"
STATUS_ID = "CmfStatus:77777777-7777-7777-7777-777777777777"

TASK_CODE = "ACME-1"
PROJECT_CODE = "acme_project"
PERSON_LOGIN = "someone@example.com"
DOCUMENT_CODE = "DOC-1"
LIST_CODE = "LST-000001"

#: Codes a live instance would resolve to internal identifiers.
RESOLVED = {
    TASK_CODE: TASK_ID,
    PROJECT_CODE: PROJECT_ID,
    PERSON_LOGIN: PERSON_ID,
    DOCUMENT_CODE: DOCUMENT_ID,
    LIST_CODE: LIST_ID,
}

# --- Response shapes ---------------------------------------------------------

#: A status is a CmfStatus relation. Its human-facing name ("Backlog") and its
#: type ("OPEN") are different fields, and the type is also cached on the task
#: as ``cache_status_type`` — filtering the relation by a type name matches
#: nothing.
CMF_STATUS = {
    "id": STATUS_ID,
    "class_name": "CmfStatus",
    "name": "Backlog",
    "code": "backlog",
    "status_type": "OPEN",
    "color": "#a0a0a0",
    "text": None,
    "parent_id": None,
    "project_id": PROJECT_ID,
}

#: A person relation. ``code`` and ``login`` carry the same login string, while
#: the entity is still addressed by ``id``.
CMF_PERSON = {
    "id": PERSON_ID,
    "class_name": "CmfPerson",
    "login": PERSON_LOGIN,
    "code": PERSON_LOGIN,
    "name": "Test Person",
    "parent_id": None,
    "project_id": None,
    "_acl_fields": {"login": "readonly", "code": "readonly"},
    "_acl_obj": "readonly",
}

#: What ``CmfTask.get`` returns with no explicit field list. Note the absence of
#: ``text``: the description has to be requested, which is why the tools pass
#: TASK_DETAIL_FIELDS.
TASK_DEFAULT_FIELDS = {
    "id": TASK_ID,
    "class_name": "CmfTask",
    "code": TASK_CODE,
    "name": "Test Task",
    "parent_id": PROJECT_ID,
    "project_id": PROJECT_ID,
    "cache_status_type": "OPEN",
    "cache_child_tasks_count": 0,
    "workflow_id": "CmfWorkflow:88888888-8888-8888-8888-888888888888",
    "cmf_owner_id": PERSON_ID,
}

#: The same task requested with an explicit field list: relations arrive
#: expanded, and the description arrives as raw HTML.
TASK_DETAILED = {
    **TASK_DEFAULT_FIELDS,
    "text": "<p>Test description</p>",
    "status": CMF_STATUS,
    "responsible": CMF_PERSON,
    "responsible_id": PERSON_ID,
    "lists": [],
    "deadline": None,
    "priority": 3,
}

#: A comment row as it arrives when the body fields are asked for. ``code`` and
#: ``name`` really are null on comments — they are addressed by id — and the
#: default response carries neither ``text`` nor ``cmf_created_at``, so a caller
#: that omits ``fields`` can count comments but not read them. The author is a
#: nested person under ``cmf_owner``; there is no ``author`` or ``created_by``
#: field, and no ``cmf_updated_at``.
COMMENT_ROW = {
    "id": COMMENT_ID,
    "class_name": "CmfComment",
    "code": None,
    "name": None,
    "private": False,
    "cmf_created_at": "2026-09-05T01:42:00.547012+03:00",
    "cmf_owner": CMF_PERSON,
    "cmf_owner_id": PERSON_ID,
    "parent_id": TASK_ID,
    "project_id": PROJECT_ID,
    "text": "<p>Test comment</p>",
}

#: A second comment, written later. Used to pin the order the thread reads in.
COMMENT_ROW_NEWER = {
    **COMMENT_ROW,
    "id": "CmfComment:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "cmf_created_at": "2026-09-05T09:30:24.001656+03:00",
    "text": "<p>Later comment</p>",
}

#: An audit row the current token may not read. The entry is found, but every
#: field is withheld — a caller has to tolerate this rather than treat it as an
#: empty result.
AUDIT_ROW_DENIED = {
    "id": "CmfAudit:99999999-9999-9999-9999-999999999999",
    "class_name": "CmfAudit",
    "_acl_fields": {"cmf_created_at": "deny", "parent_id": "deny"},
    "_acl_obj": "deny",
}

LIST_ROW = {
    "id": LIST_ID,
    "class_name": "CmfList",
    "code": LIST_CODE,
    "name": "Test Sprint",
    "cache_members_count": 2,
}

PROJECT_ROW = {
    "id": PROJECT_ID,
    "class_name": "CmfProject",
    "code": PROJECT_CODE,
    "name": "Test Project",
    "cache_status_type": "OPEN",
    "parent_id": None,
    "project_id": PROJECT_ID,
}


def filters_of(mock_method):
    """Pull the filter list out of a recorded client call."""
    return mock_method.call_args.kwargs["filters"]
