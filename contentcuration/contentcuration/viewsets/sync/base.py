from collections import OrderedDict

from search.viewsets.savedsearch import SavedSearchViewSet

from contentcuration.viewsets.assessmentitem import AssessmentItemViewSet
from contentcuration.viewsets.bookmark import BookmarkViewSet
from contentcuration.viewsets.channel import ChannelViewSet
from contentcuration.viewsets.channelset import ChannelSetViewSet
from contentcuration.viewsets.clipboard import ClipboardViewSet
from contentcuration.viewsets.contentnode import ContentNodeViewSet
from contentcuration.viewsets.contentnode import PrerequisitesUpdateHandler
from contentcuration.viewsets.file import FileViewSet
from contentcuration.viewsets.invitation import InvitationViewSet
from contentcuration.viewsets.sync.constants import ASSESSMENTITEM
from contentcuration.viewsets.sync.constants import BOOKMARK
from contentcuration.viewsets.sync.constants import CHANNEL
from contentcuration.viewsets.sync.constants import CHANNELSET
from contentcuration.viewsets.sync.constants import CLIPBOARD
from contentcuration.viewsets.sync.constants import CONTENTNODE
from contentcuration.viewsets.sync.constants import CONTENTNODE_PREREQUISITE
from contentcuration.viewsets.sync.constants import COPIED
from contentcuration.viewsets.sync.constants import CREATED
from contentcuration.viewsets.sync.constants import DELETED
from contentcuration.viewsets.sync.constants import EDITOR_M2M
from contentcuration.viewsets.sync.constants import FILE
from contentcuration.viewsets.sync.constants import INVITATION
from contentcuration.viewsets.sync.constants import MOVED
from contentcuration.viewsets.sync.constants import SAVEDSEARCH
from contentcuration.viewsets.sync.constants import TASK
from contentcuration.viewsets.sync.constants import UPDATED
from contentcuration.viewsets.sync.constants import USER
from contentcuration.viewsets.sync.constants import VIEWER_M2M
from contentcuration.viewsets.sync.utils import log_sync_exception
from contentcuration.viewsets.task import TaskViewSet
from contentcuration.viewsets.user import ChannelUserViewSet
from contentcuration.viewsets.user import UserViewSet


class ChangeNotAllowed(Exception):
    """
    Used to report changes that are not supported by the backend
    """

    def __init__(self, change_type, viewset_class):
        self.change_type = change_type
        self.viewset_class = viewset_class
        self.message = "Change type {} not allowed on viewset {}.".format(
            change_type, viewset_class
        )

        super(ChangeNotAllowed, self).__init__(self.message)


# Uses ordered dict behaviour to enforce operation orders
viewset_mapping = OrderedDict(
    [
        (USER, UserViewSet),
        # If a new channel has been created, then any other operations that happen
        # within that channel depend on that, so we prioritize channel operations
        (CHANNEL, ChannelViewSet),
        (BOOKMARK, BookmarkViewSet),
        (INVITATION, InvitationViewSet),
        # Tree operations require content nodes to exist, and any new assessment items
        # need to point to an existing content node
        (CONTENTNODE, ContentNodeViewSet),
        (CONTENTNODE_PREREQUISITE, PrerequisitesUpdateHandler),
        (CLIPBOARD, ClipboardViewSet),
        # The exact order of these three is not important.
        (ASSESSMENTITEM, AssessmentItemViewSet),
        (CHANNELSET, ChannelSetViewSet),
        (FILE, FileViewSet),
        (EDITOR_M2M, ChannelUserViewSet),
        (VIEWER_M2M, ChannelUserViewSet),
        (SAVEDSEARCH, SavedSearchViewSet),
        (TASK, TaskViewSet),
    ]
)

change_order = [
    # inserts
    COPIED,
    CREATED,
    # updates
    UPDATED,
    DELETED,
    MOVED,
]

table_name_indices = {
    table_name: i for i, table_name in enumerate(viewset_mapping.keys())
}


def get_table(obj):
    return obj["table"]


def get_table_sort_order(obj):
    return table_name_indices[get_table(obj)]


def get_change_type(obj):
    return obj["type"]


def get_change_order(obj):
    try:
        change_type = int(obj["type"])
    except ValueError:
        change_type = -1
    return change_order.index(change_type)


event_handlers = {
    CREATED: "create_from_changes",
    UPDATED: "update_from_changes",
    DELETED: "delete_from_changes",
    MOVED: "move_from_changes",
    COPIED: "copy_from_changes",
}


def apply_changes(changes_queryset):
    changes = changes_queryset.order_by("server_rev").select_related("created_by")
    for change in changes:
        # Assume an error, this will be updated
        # in the case there isn't!
        changed_fields = ("errored", "kwargs")
        table_name = change.table
        try:
            viewset_class = viewset_mapping[table_name]
            change_type = change.change_type
            change_type = int(change_type)
            viewset = viewset_class()
            viewset.sync_initial(change.created_by)
            if change_type in event_handlers:
                event_handler = getattr(viewset, event_handlers[change_type], None)
                if event_handler is None:
                    raise ChangeNotAllowed(change_type, viewset_class)
                errors = event_handler([change.serialize_to_change_dict()])
                if errors:
                    change.errored = True
                    change.kwargs["errors"] = errors[0]["errors"]
                else:
                    change.applied = True
                    changed_fields = ("applied",)
        except Exception as e:
            log_sync_exception(e)
            change.errored = True
            change.kwargs["errors"] = [str(e)]
        change.save(update_fields=changed_fields)
