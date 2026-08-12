"""Plastic SCM main window — QMainWindow with tab UI and drain queue."""
from __future__ import annotations

import queue
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Protocol

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QPoint,
    QSortFilterProxyModel,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QFontDatabase,
    QKeySequence,
    QShortcut,
    QStandardItem,
    QStandardItemModel,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableView,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from ._components import (
    _DT_FMT,
    AclModel,
    AttributesDialog,
    BlameDialog,
    BranchDAGWidget,
    BranchTreeModel,
    ChangesetModel,
    ConfEditorDialog,
    ConfigModel,
    CSDetailWidget,
    DiffHighlighter,
    GraphDelegate,
    GroupModel,
    HistoryDialog,
    InlineDiffPanel,
    LabelModel,
    RepoModel,
    ReviewModel,
    ShelveModel,
    SideBySideDiffDialog,
    StatusIconDelegate,
    ThreeWayMergeDialog,
    TriggerModel,
    UserModel,
    WorkspaceModel,
    XlinkModel,
    _btn,
    _DetailsPanel,
    _filter_edit,
    _make_proxy,
)
from ._conf_files import cloaked_conf_path, ignore_conf_path, write_conf
from ._models import (
    STATUS_LABELS,
    BlameLine,
    Branch,
    Changeset,
    CSDiffFile,
    Label,
    PlasticItem,
    Review,
    Revision,
    Shelve,
    WorkspaceInfo,
    _fmt_size,
)
from ._reviews import REVIEW_STATUSES

# ── Protocol ──────────────────────────────────────────────────────────────────

class PlasticViewProtocol(Protocol):
    """Interface the presenter drives. All methods are thread-safe (enqueue)."""

    def set_status_items(self, items: list[PlasticItem]) -> None: ...
    def set_changesets(self, items: list[Changeset]) -> None: ...
    def set_branches(self, items: list[Branch]) -> None: ...
    def set_labels(self, items: list[Label]) -> None: ...
    def set_shelves(self, items: list[Shelve]) -> None: ...
    def set_header(self, branch: str, repo: str) -> None: ...
    def show_error(self, msg: str) -> None: ...
    def show_diff(self, text: str) -> None: ...
    def set_status_message(self, msg: str) -> None: ...
    def set_busy(self, busy: bool) -> None: ...
    def show_history(self, path: Path, items: list[Revision]) -> None: ...
    def show_blame(self, path: Path, items: list[BlameLine]) -> None: ...
    def set_reviews(self, items: list[Review]) -> None: ...
    def set_changelist_status(self, grouped: dict[str, list[PlasticItem]]) -> None: ...
    def set_workspace_info(self, wi: object) -> None: ...
    def show_find_results(self, paths: list[Path]) -> None: ...
    def set_xlinks(self, items: list) -> None: ...
    def show_attributes(self, obj_spec: str, items: list) -> None: ...
    def show_acl(self, obj_spec: str, items: list) -> None: ...
    def set_users(self, items: list) -> None: ...
    def set_groups(self, items: list) -> None: ...
    def set_dag(self, nodes: list, branches: list) -> None: ...
    def show_merge_sides(self, path: Path, base: str, source: str, dest: str) -> None: ...
    def show_config_entries(self, items: list) -> None: ...
    def set_workspaces(self, items: list) -> None: ...
    def set_repos(self, items: list) -> None: ...
    def set_triggers(self, items: list) -> None: ...
    def set_cs_files(self, files: list) -> None: ...


# ── PlasticWindow ─────────────────────────────────────────────────────────────

class PlasticWindow(QMainWindow):
    """Top-level window for Plastic SCM. Separate window, not embedded in panels."""

    # Changes tab
    checkin_requested = Signal(object, str)   # (list[PlasticItem], comment)
    undo_requested = Signal(object)           # list[PlasticItem]
    diff_file_requested = Signal(object)      # PlasticItem
    refresh_changes = Signal()
    update_requested = Signal()

    # Changesets tab
    switch_to_cs = Signal(int)
    diff_with_prev = Signal(int)
    cs_double_clicked = Signal(int)
    cs_selected = Signal(int)
    refresh_changesets = Signal()

    # Branches tab
    switch_branch = Signal(str)
    create_branch_requested = Signal(str)
    refresh_branches = Signal()

    # Labels tab
    switch_to_label = Signal(str)
    refresh_labels = Signal()
    create_label_requested = Signal(str, int)   # (name, cs_id)
    delete_label_requested = Signal(str)
    rename_label_requested = Signal(str, str)   # (old, new)

    # Branches tab extra
    delete_branch_requested = Signal(str)
    rename_branch_requested = Signal(str, str)  # (old, new)

    # Shelves tab
    shelve_requested = Signal(object, str)    # (list[PlasticItem], comment)
    unshelve_requested = Signal(int)          # shelve_id
    refresh_shelves = Signal()

    # New actions
    merge_branch_requested = Signal(str, bool, str, bool)  # (name, preview, resolve, semantic)
    undo_changeset_requested = Signal(int)             # cs_id
    undo_all_requested = Signal()
    undo_keep_requested = Signal(object)               # list[PlasticItem]
    rollback_cs_requested = Signal(int)
    lock_requested = Signal(object)           # list[PlasticItem]
    unlock_requested = Signal(object)         # list[PlasticItem]

    # File history + blame
    history_requested = Signal(object)        # PlasticItem
    blame_requested = Signal(object)          # PlasticItem

    # Reviews tab (sidebar row 5)
    refresh_reviews = Signal()
    create_review_requested = Signal(int, str, str)   # (cs_id, title, assignee)
    edit_review_requested = Signal(int, str)           # (review_id, new_status)
    delete_review_requested = Signal(int)              # review_id

    # Changelists (from pending changes context menu)
    move_to_changelist_requested = Signal(object, str) # (list[PlasticItem], name)
    load_changelist_status_requested = Signal()

    # File ops (4.7)
    add_to_vcs_requested     = Signal(object)          # list[PlasticItem]
    remove_from_vcs_requested = Signal(object)         # list[PlasticItem]
    move_file_requested      = Signal(object, object)  # (src: Path, dst: Path)

    # Advanced diff (4.8)
    diff_cs_range_requested  = Signal(int, int)        # (cs_a, cs_b)
    diff_branch_requested    = Signal(str)
    diff_labels_requested    = Signal(str, str)        # (lb_a, lb_b)
    diff_shelve_requested    = Signal(int)

    # CS edit comment (4.10)
    edit_cs_comment_requested = Signal(int, str)       # (cs_id, new_comment)

    # Find (4.11)
    find_files_requested = Signal(str)

    # Xlinks (5.4)
    refresh_xlinks = Signal()
    add_xlink_requested = Signal(str, str, str)    # path, server, repo
    remove_xlink_requested = Signal(str)            # path

    # Replication (5.5)
    push_replication_requested = Signal(str, str)  # server, repo
    pull_replication_requested = Signal(str)        # server
    replica_pkg_create_requested = Signal(str)      # output_path
    replica_pkg_import_requested = Signal(str)      # file_path

    # Attributes (5.6)
    load_attributes_requested = Signal(str)         # obj_spec
    set_attribute_requested = Signal(str, str, str) # obj_spec, name, value
    delete_attribute_requested = Signal(str, str)   # obj_spec, name

    # ACL (5.7)
    load_acl_requested = Signal(str)                # obj_spec
    set_acl_requested = Signal(str, str, str)       # obj_spec, principal, permission
    delete_acl_requested = Signal(str, str)         # obj_spec, principal

    # Users / Groups (5.8)
    load_users_requested = Signal()
    add_user_requested = Signal(str, str)           # name, email
    delete_user_requested = Signal(str)             # name
    load_groups_requested = Signal()
    add_group_requested = Signal(str)               # name
    delete_group_requested = Signal(str)            # name
    add_group_member_requested = Signal(str, str)   # group, user

    # Branch DAG (5.1)
    refresh_dag = Signal()

    # Three-way merge viewer (5.2)
    merge_view_requested = Signal(object)           # PlasticItem

    # Preferences / cm config (#8)
    load_config_requested = Signal()
    set_config_requested = Signal(str, str)         # key, value

    # Partial workspaces (#5)
    load_partial_status_requested = Signal()
    configure_partial_requested = Signal()
    add_partial_requested = Signal(str)             # path
    remove_partial_requested = Signal(str)          # path

    # Workspaces & Repos (#1)
    refresh_workspaces = Signal()
    create_workspace_requested = Signal(str, str, str, str)  # name, path, server, repo
    delete_workspace_requested = Signal(str)
    refresh_repos = Signal()
    create_repo_requested = Signal(str)
    delete_repo_requested = Signal(str)

    # Triggers (#6)
    refresh_triggers = Signal()
    create_trigger_requested = Signal(str, str, str, str)  # name, event, filter, command
    delete_trigger_requested = Signal(str)                 # trigger_id

    # Git Sync (#4)
    sync_git_requested = Signal(str)   # url
    refresh_git_sync = Signal()

    _DRAIN_LIMIT = 50  # max queue items processed per 100ms tick

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Plastic SCM")
        self.resize(900, 600)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._status_model = QStandardItemModel()
        self._status_model.setHorizontalHeaderLabels(
            ["Item", "Status", "Size", "Date modified"]
        )
        self._changeset_model = ChangesetModel()
        self._graph_delegate = GraphDelegate()
        self._branch_tree = BranchTreeModel()
        self._label_model = LabelModel()
        self._shelve_model = ShelveModel()
        self._review_model = ReviewModel()
        self._xlink_model = XlinkModel()
        self._acl_model = AclModel()
        self._user_model = UserModel()
        self._group_model = GroupModel()
        self._config_model = ConfigModel()
        self._workspace_model = WorkspaceModel()
        self._repo_model = RepoModel()
        self._trigger_model = TriggerModel()

        # Thread-safe drain queue: presenter threads → main-thread UI
        self._queue: queue.SimpleQueue[tuple[str, object]] = queue.SimpleQueue()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._drain)
        self._timer.start(100)

        # State for new features
        self._prev_page: int = 0
        self._group_mode: int = 0   # 0=dir, 1=status, 2=changelist
        self._last_status_items: list[PlasticItem] = []
        self._last_changelist_status: dict[str, list[PlasticItem]] = {}
        self._wk_path: Path | None = None  # set from workspace_info; used by conf-file editors
        self._inline_diff_pending = False
        self._pending_diff_item: PlasticItem | None = None
        self._diff_debounce = QTimer(self)
        self._diff_debounce.setSingleShot(True)
        self._diff_debounce.setInterval(200)
        self._diff_debounce.timeout.connect(self._emit_pending_diff)

        self._build()
        self.statusBar().showMessage("Ready")

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────────
        header_bar = QWidget()
        header_bar.setObjectName("plastic_header")
        h_lay = QHBoxLayout(header_bar)
        h_lay.setContentsMargins(12, 6, 12, 6)
        self._header_label = QLabel("Branch: —   |   Repo: —")
        self._header_label.setTextFormat(Qt.TextFormat.PlainText)
        h_lay.addWidget(self._header_label)
        h_lay.addStretch()
        find_btn = QPushButton("Find Files…")
        find_btn.clicked.connect(self._on_find_files)
        h_lay.addWidget(find_btn)
        self._progress = QProgressBar()
        self._progress.setMaximum(0)   # indeterminate pulse
        self._progress.setFixedWidth(120)
        self._progress.hide()
        h_lay.addWidget(self._progress)
        root.addWidget(header_bar)

        # ── Splitter: sidebar | stacked content ───────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter)

        # Sidebar nav list
        self._nav = QListWidget()
        self._nav.setObjectName("plastic_sidebar")
        self._nav.setFixedWidth(160)
        self._nav.setFrameShape(QFrame.Shape.NoFrame)
        self._nav.setSpacing(2)
        for label in (
            "Pending Changes", "Changesets", "Branches", "Labels", "Shelves",
            "Reviews", "Xlinks", "Admin", "Branch DAG",
            "Workspaces & Repos", "Triggers", "Git Sync",
        ):
            self._nav.addItem(label)
        self._nav.setCurrentRow(0)
        splitter.addWidget(self._nav)

        # Content stack — rows match sidebar; last row = diff (via _diff_page_index)
        self._stack = QStackedWidget()
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Page 0 — Pending Changes (tree + inline comment + toolbar)
        self._stack.addWidget(self._build_pending_changes_page())

        # Pages 1-7 — toolbar-at-top + filter bar + details panel
        self._stack.addWidget(self._build_changesets_page())
        self._stack.addWidget(self._build_branches_page())
        self._stack.addWidget(self._build_labels_page())
        self._stack.addWidget(self._build_shelves_page())
        self._stack.addWidget(self._build_reviews_page())   # index 5
        self._stack.addWidget(self._build_xlinks_page())   # index 6
        self._stack.addWidget(self._build_admin_page())    # index 7
        self._stack.addWidget(self._build_dag_page())           # index 8
        self._stack.addWidget(self._build_workspaces_page())   # index 9
        self._stack.addWidget(self._build_triggers_page())     # index 10
        self._stack.addWidget(self._build_git_sync_page())     # index 11

        # Page 12 — Diff (not in sidebar; auto-switched by show_diff)
        self._diff_view = QPlainTextEdit()
        self._diff_view.setReadOnly(True)
        self._diff_view.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        DiffHighlighter(self._diff_view.document())
        self._diff_page_index = self._stack.addWidget(self._build_diff_page())

        self._nav.currentRowChanged.connect(self._stack.setCurrentIndex)
        self._build_shortcuts()

    @staticmethod
    def _make_table(model: QAbstractItemModel, *, multi_select: bool = False) -> QTableView:
        t = QTableView()
        t.setModel(model)
        t.setAlternatingRowColors(True)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
            if multi_select
            else QAbstractItemView.SelectionMode.SingleSelection
        )
        t.horizontalHeader().setStretchLastSection(True)
        t.verticalHeader().hide()
        t.setShowGrid(False)
        return t

    @staticmethod
    def _make_tab(
        table: QTableView, buttons: list[tuple[str, Callable]]
    ) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(table)
        btn_row = QHBoxLayout()
        for label, slot in buttons:
            b = QPushButton(label)
            b.clicked.connect(slot)
            btn_row.addWidget(b)
        btn_row.addStretch()
        lay.addLayout(btn_row)
        return w

    def _build_pending_changes_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(6)

        def _sep() -> QFrame:
            f = QFrame()
            f.setFrameShape(QFrame.Shape.VLine)
            f.setFrameShadow(QFrame.Shadow.Sunken)
            return f

        # Toolbar with grouped buttons
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)
        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.clicked.connect(self.refresh_changes.emit)
        checkin_btn = QPushButton("Check in")
        checkin_btn.setDefault(True)
        checkin_btn.clicked.connect(self._on_checkin)
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self._on_undo)
        diff_btn = QPushButton("Diff")
        diff_btn.clicked.connect(self._on_diff_file)
        update_btn = QPushButton("Update")
        update_btn.clicked.connect(self.update_requested.emit)
        shelve_btn = QPushButton("Shelve")
        shelve_btn.clicked.connect(self._on_shelve)
        lock_btn = QPushButton("Lock")
        lock_btn.clicked.connect(self._on_lock)
        unlock_btn = QPushButton("Unlock")
        unlock_btn.clicked.connect(self._on_unlock)
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(_sep())
        toolbar.addWidget(checkin_btn)
        toolbar.addWidget(undo_btn)
        toolbar.addWidget(_sep())
        toolbar.addWidget(diff_btn)
        toolbar.addWidget(update_btn)
        toolbar.addWidget(shelve_btn)
        toolbar.addWidget(_sep())
        toolbar.addWidget(lock_btn)
        toolbar.addWidget(unlock_btn)
        toolbar.addStretch()
        self._group_combo = QComboBox()
        self._group_combo.addItems(["Group: Directory", "Group: Status", "Group: Changelist"])
        self._group_combo.currentIndexChanged.connect(self._on_change_grouping)
        toolbar.addWidget(self._group_combo)
        lay.addLayout(toolbar)

        # Inline comment
        self._comment_edit = QLineEdit()
        self._comment_edit.setPlaceholderText(
            "Add a comment to your check-in or shelve..."
        )
        lay.addWidget(self._comment_edit)

        # Item count label
        self._changes_count = QLabel("Changed items")
        lay.addWidget(self._changes_count)

        # Tree view
        self._status_tree = QTreeView()
        self._status_tree.setModel(self._status_model)
        self._status_tree.setAlternatingRowColors(True)
        self._status_tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._status_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._status_tree.header().setStretchLastSection(True)
        self._status_tree.setUniformRowHeights(True)
        self._status_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._status_tree.customContextMenuRequested.connect(self._pending_context_menu)
        self._status_tree.setItemDelegateForColumn(1, StatusIconDelegate(self._status_tree))
        h = self._status_tree.header()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        h.resizeSection(1, 28)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.resizeSection(2, 80)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h.resizeSection(3, 140)
        h.setStretchLastSection(False)

        # Inline diff panel in splitter
        self._pending_diff_panel = InlineDiffPanel()
        split = QSplitter(Qt.Orientation.Vertical)
        split.setChildrenCollapsible(False)
        split.addWidget(self._status_tree)
        split.addWidget(self._pending_diff_panel)
        split.setSizes([350, 250])
        lay.addWidget(split)

        # Wire selection → debounced inline diff
        self._status_tree.selectionModel().currentChanged.connect(self._on_pending_selection)

        return w

    def _build_changesets_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        tb = QHBoxLayout()
        tb.setSpacing(6)
        _btn(tb, "Refresh", self.refresh_changesets.emit)
        _btn(tb, "Switch to CS", self._on_switch_cs)
        _btn(tb, "Diff with prev", self._on_diff_prev)
        _btn(tb, "Rollback", self._on_rollback_cs)
        _btn(tb, "Undo CS", self._on_undo_changeset)
        _btn(tb, "Undo All", self.undo_all_requested.emit)
        tb.addStretch()
        tb.addWidget(QLabel("Filter:"))
        cs_filter = _filter_edit()
        tb.addWidget(cs_filter)
        lay.addLayout(tb)

        self._cs_proxy = _make_proxy(self._changeset_model)
        cs_filter.textChanged.connect(self._cs_proxy.setFilterFixedString)

        self._cs_table = self._make_table(self._cs_proxy)
        self._cs_table.setItemDelegateForColumn(0, self._graph_delegate)
        ch = self._cs_table.horizontalHeader()
        ch.setStretchLastSection(False)
        ch.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        ch.resizeSection(0, 80)    # graph
        ch.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        ch.resizeSection(1, 60)    # CS#
        ch.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        ch.resizeSection(2, 130)   # Date
        ch.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        ch.resizeSection(3, 120)   # Author
        ch.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Comment
        ch.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        ch.resizeSection(5, 100)   # Branch
        self._cs_table.doubleClicked.connect(self._on_cs_double_click)
        self._cs_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._cs_table.customContextMenuRequested.connect(self._cs_context_menu)

        self._cs_detail = CSDetailWidget()

        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self._cs_table)
        split.addWidget(self._cs_detail)
        split.setSizes([300, 300])
        lay.addWidget(split)

        self._cs_table.selectionModel().currentRowChanged.connect(self._on_cs_selection)
        return page

    def _build_branches_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        tb = QHBoxLayout()
        tb.setSpacing(6)
        _btn(tb, "Refresh", self.refresh_branches.emit)
        _btn(tb, "Switch", self._on_switch_branch)
        _btn(tb, "Create…", self._on_create_branch)
        _btn(tb, "Merge", self._on_merge_branch)
        _btn(tb, "Delete", self._on_delete_branch)
        _btn(tb, "Rename…", self._on_rename_branch)
        tb.addStretch()
        tb.addWidget(QLabel("Filter:"))
        br_filter = _filter_edit()
        tb.addWidget(br_filter)
        lay.addLayout(tb)

        self._branch_proxy = QSortFilterProxyModel()
        self._branch_proxy.setSourceModel(self._branch_tree.model)
        self._branch_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._branch_proxy.setFilterRole(Qt.ItemDataRole.DisplayRole)
        self._branch_proxy.setRecursiveFilteringEnabled(True)
        br_filter.textChanged.connect(self._branch_proxy.setFilterFixedString)

        self._branch_view = QTreeView()
        self._branch_view.setModel(self._branch_proxy)
        self._branch_view.setAlternatingRowColors(True)
        self._branch_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._branch_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._branch_view.header().setStretchLastSection(True)
        self._branch_view.setUniformRowHeights(True)
        self._branch_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._branch_view.customContextMenuRequested.connect(self._branch_context_menu)
        bh = self._branch_view.header()
        bh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        bh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        bh.resizeSection(1, 130)
        bh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        bh.resizeSection(2, 150)
        bh.setStretchLastSection(False)
        self._branch_details = _DetailsPanel()

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._branch_view)
        split.addWidget(self._branch_details)
        split.setSizes([650, 280])
        lay.addWidget(split)

        self._branch_view.selectionModel().currentChanged.connect(self._on_branch_selection)
        return page

    def _build_labels_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        tb = QHBoxLayout()
        tb.setSpacing(6)
        _btn(tb, "Refresh", self.refresh_labels.emit)
        _btn(tb, "Switch to Label", self._on_switch_label)
        _btn(tb, "Create…", self._on_create_label)
        _btn(tb, "Delete", self._on_delete_label)
        _btn(tb, "Rename…", self._on_rename_label)
        tb.addStretch()
        tb.addWidget(QLabel("Filter:"))
        lbl_filter = _filter_edit()
        tb.addWidget(lbl_filter)
        lay.addLayout(tb)

        self._label_proxy = _make_proxy(self._label_model)
        lbl_filter.textChanged.connect(self._label_proxy.setFilterFixedString)

        self._label_table = self._make_table(self._label_proxy)
        self._label_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._label_table.customContextMenuRequested.connect(self._label_context_menu)
        self._label_details = _DetailsPanel()

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._label_table)
        split.addWidget(self._label_details)
        split.setSizes([650, 280])
        lay.addWidget(split)

        self._label_table.selectionModel().currentRowChanged.connect(self._on_label_selection)
        return page

    def _build_shelves_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        tb = QHBoxLayout()
        tb.setSpacing(6)
        _btn(tb, "Refresh", self.refresh_shelves.emit)
        _btn(tb, "Apply (Unshelve)", self._on_unshelve)
        tb.addStretch()
        tb.addWidget(QLabel("Filter:"))
        shelve_filter = _filter_edit()
        tb.addWidget(shelve_filter)
        lay.addLayout(tb)

        self._shelve_proxy = _make_proxy(self._shelve_model)
        shelve_filter.textChanged.connect(self._shelve_proxy.setFilterFixedString)

        self._shelve_table = self._make_table(self._shelve_proxy)
        self._shelve_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._shelve_table.customContextMenuRequested.connect(self._shelve_context_menu)
        self._shelve_details = _DetailsPanel()

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._shelve_table)
        split.addWidget(self._shelve_details)
        split.setSizes([650, 280])
        lay.addWidget(split)

        self._shelve_table.selectionModel().currentRowChanged.connect(self._on_shelve_selection)
        return page

    def _build_reviews_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        tb = QHBoxLayout()
        tb.setSpacing(6)
        _btn(tb, "Refresh", self.refresh_reviews.emit)
        _btn(tb, "Create…", self._on_create_review)
        _btn(tb, "Edit Status", self._on_edit_review_status)
        _btn(tb, "Delete", self._on_delete_review)
        tb.addStretch()
        tb.addWidget(QLabel("Filter:"))
        rev_filter = _filter_edit()
        tb.addWidget(rev_filter)
        lay.addLayout(tb)

        self._review_proxy = _make_proxy(self._review_model)
        rev_filter.textChanged.connect(self._review_proxy.setFilterFixedString)

        self._review_table = self._make_table(self._review_proxy)
        self._review_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._review_table.customContextMenuRequested.connect(self._review_context_menu)
        self._review_details = _DetailsPanel()

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._review_table)
        split.addWidget(self._review_details)
        split.setSizes([650, 280])
        lay.addWidget(split)

        self._review_table.selectionModel().currentRowChanged.connect(self._on_review_selection)
        return page

    def _build_xlinks_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        tb = QHBoxLayout()
        tb.setSpacing(6)
        _btn(tb, "Refresh", self.refresh_xlinks.emit)
        _btn(tb, "Add…", self._on_add_xlink)
        _btn(tb, "Remove", self._on_remove_xlink)
        tb.addStretch()
        tb.addWidget(QLabel("Filter:"))
        xlink_filter = _filter_edit()
        tb.addWidget(xlink_filter)
        lay.addLayout(tb)

        self._xlink_proxy = _make_proxy(self._xlink_model)
        xlink_filter.textChanged.connect(self._xlink_proxy.setFilterFixedString)

        self._xlink_table = self._make_table(self._xlink_proxy)
        lay.addWidget(self._xlink_table)
        return page

    def _build_admin_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        # ACL section
        tb_acl = QHBoxLayout()
        tb_acl.setSpacing(6)
        self._acl_spec_edit = QLineEdit()
        self._acl_spec_edit.setPlaceholderText("Object spec (e.g. br:/main)")
        tb_acl.addWidget(self._acl_spec_edit)
        _btn(tb_acl, "Load ACL", self._on_load_acl)
        _btn(tb_acl, "Set…", self._on_set_acl)
        _btn(tb_acl, "Delete", self._on_delete_acl)
        tb_acl.addStretch()
        tb_acl.addWidget(QLabel("ACLs"))
        lay.addLayout(tb_acl)

        self._acl_proxy = _make_proxy(self._acl_model)
        self._acl_table = self._make_table(self._acl_proxy)
        lay.addWidget(self._acl_table)

        # Users section
        tb_users = QHBoxLayout()
        tb_users.setSpacing(6)
        _btn(tb_users, "Load Users", self.load_users_requested.emit)
        _btn(tb_users, "Add User…", self._on_add_user)
        _btn(tb_users, "Delete User", self._on_delete_user)
        tb_users.addStretch()
        tb_users.addWidget(QLabel("Users"))
        lay.addLayout(tb_users)

        self._user_proxy = _make_proxy(self._user_model)
        self._user_table = self._make_table(self._user_proxy)
        lay.addWidget(self._user_table)

        # Groups section
        tb_groups = QHBoxLayout()
        tb_groups.setSpacing(6)
        _btn(tb_groups, "Load Groups", self.load_groups_requested.emit)
        _btn(tb_groups, "Add Group…", self._on_add_group)
        _btn(tb_groups, "Delete Group", self._on_delete_group)
        _btn(tb_groups, "Add Member…", self._on_add_group_member)
        tb_groups.addStretch()
        tb_groups.addWidget(QLabel("Groups"))
        lay.addLayout(tb_groups)

        self._group_proxy = _make_proxy(self._group_model)
        self._group_table = self._make_table(self._group_proxy)
        lay.addWidget(self._group_table)

        # Package Replication section (#9)
        tb_pkg = QHBoxLayout()
        tb_pkg.setSpacing(6)
        self._pkg_path_edit = QLineEdit()
        self._pkg_path_edit.setPlaceholderText("Package file path…")
        tb_pkg.addWidget(self._pkg_path_edit)
        _btn(tb_pkg, "Create Package", self._on_pkg_create)
        _btn(tb_pkg, "Import Package…", self._on_pkg_import)
        tb_pkg.addStretch()
        tb_pkg.addWidget(QLabel("Package Replication"))
        lay.addLayout(tb_pkg)

        # Workspace config files section (#2 / #3)
        tb_conf = QHBoxLayout()
        tb_conf.setSpacing(6)
        _btn(tb_conf, "Edit ignore.conf", self._on_edit_ignore)
        _btn(tb_conf, "Edit cloaked.conf", self._on_edit_cloaked)
        tb_conf.addStretch()
        tb_conf.addWidget(QLabel("Workspace Config Files"))
        lay.addLayout(tb_conf)

        # Preferences section (#8)
        tb_cfg = QHBoxLayout()
        tb_cfg.setSpacing(6)
        _btn(tb_cfg, "Load Config", self.load_config_requested.emit)
        _btn(tb_cfg, "Set…", self._on_set_config)
        tb_cfg.addStretch()
        tb_cfg.addWidget(QLabel("Preferences"))
        lay.addLayout(tb_cfg)

        self._config_proxy = _make_proxy(self._config_model)
        self._config_table = self._make_table(self._config_proxy)
        lay.addWidget(self._config_table)

        # Partial Workspace section (#5)
        tb_partial = QHBoxLayout()
        tb_partial.setSpacing(6)
        _btn(tb_partial, "Status", self.load_partial_status_requested.emit)
        _btn(tb_partial, "Configure", self.configure_partial_requested.emit)
        _btn(tb_partial, "Add Path…", self._on_partial_add)
        _btn(tb_partial, "Remove Path…", self._on_partial_remove)
        tb_partial.addStretch()
        tb_partial.addWidget(QLabel("Partial Workspace"))
        lay.addLayout(tb_partial)

        return page

    def _build_dag_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 4, 0, 0)
        tb = QHBoxLayout()
        _btn(tb, "Refresh", self.refresh_dag.emit)
        tb.addStretch()
        lay.addLayout(tb)
        self._dag_widget = BranchDAGWidget()
        lay.addWidget(self._dag_widget)
        return w

    def _build_workspaces_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: workspaces
        wk_widget = QWidget()
        wk_lay = QVBoxLayout(wk_widget)
        wk_lay.setContentsMargins(0, 0, 4, 0)
        tb_wk = QHBoxLayout()
        tb_wk.setSpacing(6)
        _btn(tb_wk, "Refresh", self.refresh_workspaces.emit)
        _btn(tb_wk, "Create…", self._on_create_workspace)
        _btn(tb_wk, "Delete", self._on_delete_workspace)
        tb_wk.addStretch()
        tb_wk.addWidget(QLabel("Workspaces"))
        wk_lay.addLayout(tb_wk)
        self._wk_entry_proxy = _make_proxy(self._workspace_model)
        self._wk_entry_table = self._make_table(self._wk_entry_proxy)
        wk_lay.addWidget(self._wk_entry_table)
        splitter.addWidget(wk_widget)

        # Right: repos
        repo_widget = QWidget()
        repo_lay = QVBoxLayout(repo_widget)
        repo_lay.setContentsMargins(4, 0, 0, 0)
        tb_repo = QHBoxLayout()
        tb_repo.setSpacing(6)
        _btn(tb_repo, "Refresh", self.refresh_repos.emit)
        _btn(tb_repo, "Create…", self._on_create_repo)
        _btn(tb_repo, "Delete", self._on_delete_repo)
        tb_repo.addStretch()
        tb_repo.addWidget(QLabel("Repositories"))
        repo_lay.addLayout(tb_repo)
        self._repo_proxy = _make_proxy(self._repo_model)
        self._repo_table = self._make_table(self._repo_proxy)
        repo_lay.addWidget(self._repo_table)
        splitter.addWidget(repo_widget)

        lay.addWidget(splitter)
        return page

    def _build_triggers_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        tb = QHBoxLayout()
        tb.setSpacing(6)
        _btn(tb, "Refresh", self.refresh_triggers.emit)
        _btn(tb, "Create…", self._on_create_trigger)
        _btn(tb, "Delete", self._on_delete_trigger)
        tb.addStretch()
        lay.addLayout(tb)

        self._trigger_proxy = _make_proxy(self._trigger_model)
        self._trigger_table = self._make_table(self._trigger_proxy)
        lay.addWidget(self._trigger_table)
        return page

    def _build_git_sync_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)
        tb = QHBoxLayout()
        tb.setSpacing(6)
        self._git_url_edit = QLineEdit()
        self._git_url_edit.setPlaceholderText("Git remote URL…")
        tb.addWidget(self._git_url_edit)
        _btn(tb, "Sync", self._on_sync_git)
        _btn(tb, "Status", self.refresh_git_sync.emit)
        lay.addLayout(tb)
        lay.addStretch()
        return w

    def _build_diff_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 4, 0, 0)
        btn_row = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self._on_back_from_diff)
        back_btn.setFixedWidth(90)
        btn_row.addWidget(back_btn)
        sbs_btn = QPushButton("Side-by-side")
        sbs_btn.clicked.connect(self._on_sbs_diff)
        btn_row.addWidget(sbs_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)
        lay.addWidget(self._diff_view)
        return w

    # ── Keyboard shortcuts ────────────────────────────────────────────────────

    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence("F5"),     self, self._on_refresh_current)
        QShortcut(QKeySequence("Ctrl+I"), self, self._on_checkin_if_on_changes)
        QShortcut(QKeySequence("Ctrl+D"), self, self._on_diff_if_on_changes)
        QShortcut(QKeySequence("Escape"), self, self._on_back_from_diff)
        QShortcut(QKeySequence("Ctrl+F"), self, self._on_find_files)

    def _on_refresh_current(self) -> None:
        _signals = [
            self.refresh_changes, self.refresh_changesets, self.refresh_branches,
            self.refresh_labels, self.refresh_shelves, self.refresh_reviews,
            self.refresh_xlinks, None, self.refresh_dag,
            self.refresh_workspaces, self.refresh_triggers, self.refresh_git_sync,
        ]
        idx = self._stack.currentIndex()
        if idx == 7:
            self.load_users_requested.emit()
            self.load_groups_requested.emit()
        elif idx == 9:
            self.refresh_workspaces.emit()
            self.refresh_repos.emit()
        elif 0 <= idx < len(_signals) and _signals[idx]:
            _signals[idx].emit()

    def _on_checkin_if_on_changes(self) -> None:
        if self._stack.currentIndex() == 0:
            self._on_checkin()

    def _on_diff_if_on_changes(self) -> None:
        if self._stack.currentIndex() == 0:
            self._on_diff_file()

    def _on_back_from_diff(self) -> None:
        self._inline_diff_pending = False
        if self._stack.currentIndex() == self._diff_page_index:
            self._stack.setCurrentIndex(self._prev_page)

    def _on_pending_selection(self, current: QModelIndex, _: QModelIndex) -> None:
        item = self._status_model.itemFromIndex(current)
        if item and (plastic := item.data(Qt.ItemDataRole.UserRole)):
            self._pending_diff_item = plastic
            self._diff_debounce.start()
        else:
            self._pending_diff_panel.clear()
            self._pending_diff_item = None

    def _emit_pending_diff(self) -> None:
        if self._pending_diff_item:
            from ._diff import is_image
            if is_image(self._pending_diff_item.path):
                self._pending_diff_panel.show_image(self._pending_diff_item.path)
            else:
                self._inline_diff_pending = True
                self.diff_file_requested.emit(self._pending_diff_item)

    # ── Context menus ─────────────────────────────────────────────────────────

    def _show_context_menu(
        self,
        view: QAbstractItemView,
        pos: QPoint,
        actions: list[tuple[str, Callable]],
    ) -> None:
        menu = QMenu(self)
        for label, slot in actions:
            menu.addAction(label, slot)
        menu.popup(view.viewport().mapToGlobal(pos))

    def _pending_context_menu(self, pos: QPoint) -> None:
        self._show_context_menu(self._status_tree, pos, [
            ("Check in",             self._on_checkin),
            ("Diff",                 self._on_diff_file),
            ("Undo",                 self._on_undo),
            ("Undo (keep local)",    self._on_undo_keep),
            ("Lock",                 self._on_lock),
            ("Unlock",               self._on_unlock),
            ("Shelve",               self._on_shelve),
            ("View History",         self._on_view_history),
            ("Blame",                self._on_blame),
            ("3-Way Merge…",         self._on_merge_view),
            ("Move to changelist…",  self._on_move_to_changelist),
            ("Add to VCS",           self._on_add_to_vcs),
            ("Remove from VCS",      self._on_remove_from_vcs),
            ("Move/Rename…",         self._on_move_file),
        ])

    def _cs_context_menu(self, pos: QPoint) -> None:
        self._show_context_menu(self._cs_table, pos, [
            ("Switch to CS",  self._on_switch_cs),
            ("Diff CS",       self._on_diff_prev),
            ("Diff CS Range…",self._on_diff_cs_range),
            ("Rollback",      self._on_rollback_cs),
            ("Edit Comment…", self._on_edit_cs_comment),
        ])

    def _branch_context_menu(self, pos: QPoint) -> None:
        self._show_context_menu(self._branch_view, pos, [
            ("Switch",          self._on_switch_branch),
            ("Merge",           self._on_merge_branch),
            ("Diff Branch",     self._on_diff_branch),
            ("Create Branch…",  self._on_create_branch),
            ("Delete",          self._on_delete_branch),
            ("Rename…",         self._on_rename_branch),
            ("View in DAG",     self._on_view_branch_in_dag),
        ])

    def _label_context_menu(self, pos: QPoint) -> None:
        self._show_context_menu(self._label_table, pos, [
            ("Switch to Label", self._on_switch_label),
            ("Diff Labels…",    self._on_diff_labels),
            ("Create…",         self._on_create_label),
            ("Delete",          self._on_delete_label),
            ("Rename…",         self._on_rename_label),
        ])

    def _shelve_context_menu(self, pos: QPoint) -> None:
        self._show_context_menu(self._shelve_table, pos, [
            ("Apply (Unshelve)", self._on_unshelve),
            ("Diff Shelve",      self._on_diff_shelve),
            ("Delete",           lambda: None),   # ponytail: stub, wire delete signal when cm shelve delete is implemented
        ])

    def _review_context_menu(self, pos: QPoint) -> None:
        self._show_context_menu(self._review_table, pos, [
            ("Edit Status",  self._on_edit_review_status),
            ("Delete",       self._on_delete_review),
        ])

    # ── Selection → details ───────────────────────────────────────────────────

    def _on_cs_selection(self, current: QModelIndex, _: QModelIndex) -> None:
        src = self._cs_proxy.mapToSource(current)
        if item := self._changeset_model.item_at(src.row()):
            self._cs_detail.load_cs(item)
            self.cs_selected.emit(item.cs_id)
        else:
            self._cs_detail.clear()

    def _on_branch_selection(self, current: QModelIndex, _: QModelIndex) -> None:
        src = self._branch_proxy.mapToSource(current)
        if br := self._branch_tree.branch_at(src):
            self._branch_details.show_branch(br)
        else:
            self._branch_details.clear()

    def _on_label_selection(self, current: QModelIndex, _: QModelIndex) -> None:
        src = self._label_proxy.mapToSource(current)
        if item := self._label_model.item_at(src.row()):
            self._label_details.show_label(item)
        else:
            self._label_details.clear()

    def _on_shelve_selection(self, current: QModelIndex, _: QModelIndex) -> None:
        src = self._shelve_proxy.mapToSource(current)
        if item := self._shelve_model.item_at(src.row()):
            self._shelve_details.show_shelve(item)
        else:
            self._shelve_details.clear()

    def _on_review_selection(self, current: QModelIndex, _: QModelIndex) -> None:
        src = self._review_proxy.mapToSource(current)
        if item := self._review_model.item_at(src.row()):
            self._review_details.show_review(item)
        else:
            self._review_details.clear()

    # ── Tree population ───────────────────────────────────────────────────────

    def _make_file_row(self, plastic: PlasticItem) -> list[QStandardItem]:
        name_item = QStandardItem(plastic.path.name)
        name_item.setCheckable(True)
        name_item.setCheckState(Qt.CheckState.Checked)
        name_item.setData(plastic, Qt.ItemDataRole.UserRole)
        size_str = date_str = "—"
        try:
            st = plastic.path.stat()
            size_str = _fmt_size(st.st_size)
            date_str = datetime.fromtimestamp(st.st_mtime).strftime(_DT_FMT)
        except OSError:
            pass
        status_item = QStandardItem("")
        status_item.setData(plastic, Qt.ItemDataRole.UserRole)
        return [name_item, status_item,
                QStandardItem(size_str), QStandardItem(date_str)]

    def _build_status_tree(self, items: list[PlasticItem]) -> None:
        self._last_status_items = items
        match self._group_mode:
            case 1: self._build_by_status(items)
            case 2: self._build_by_changelist(self._last_changelist_status)
            case _: self._build_by_dir(items)
        n = len(items)
        self._changes_count.setText(f"Changed items — {n} item{'s' if n != 1 else ''}")

    def _build_by_dir(self, items: list[PlasticItem]) -> None:
        self._status_model.removeRows(0, self._status_model.rowCount())
        by_dir: dict[Path, list[PlasticItem]] = defaultdict(list)
        for item in items:
            by_dir[item.path.parent].append(item)
        for dir_path, dir_items in sorted(by_dir.items()):
            try:
                display = str(dir_path.relative_to(self._wk_path)) if self._wk_path else str(dir_path)
            except ValueError:
                display = str(dir_path)
            label = f"{display}  ({len(dir_items)})"
            dir_row = [QStandardItem(label), QStandardItem(""), QStandardItem(""), QStandardItem("")]
            dir_row[0].setFlags(Qt.ItemFlag.ItemIsEnabled)
            for plastic in sorted(dir_items, key=lambda p: p.path.name):
                dir_row[0].appendRow(self._make_file_row(plastic))
            self._status_model.appendRow(dir_row)
        self._status_tree.expandAll()

    def _build_by_status(self, items: list[PlasticItem]) -> None:
        """Group pending items by status code (CO, AD, MO, DE, etc.)."""
        self._status_model.removeRows(0, self._status_model.rowCount())
        by_status: dict[str, list[PlasticItem]] = defaultdict(list)
        for item in items:
            by_status[item.status].append(item)
        for status, group in sorted(by_status.items()):
            label = STATUS_LABELS.get(status, status).title()
            header = f"{label} ({len(group)})"
            dir_row = [QStandardItem(header), QStandardItem(""), QStandardItem(""), QStandardItem("")]
            dir_row[0].setFlags(Qt.ItemFlag.ItemIsEnabled)
            for plastic in sorted(group, key=lambda p: p.path.name):
                dir_row[0].appendRow(self._make_file_row(plastic))
            self._status_model.appendRow(dir_row)
        self._status_tree.expandAll()

    def _on_change_grouping(self, mode: int) -> None:
        self._group_mode = mode
        if mode == 2:
            self.load_changelist_status_requested.emit()
        else:
            self._build_status_tree(self._last_status_items)

    def _build_by_changelist(self, grouped: dict[str, list[PlasticItem]]) -> None:
        """Group pending items by changelist name. Unlisted items go to '(default)'."""
        self._status_model.removeRows(0, self._status_model.rowCount())
        # All items from last status that are in some changelist
        in_cl: set[Path] = {i.path for items in grouped.values() for i in items}
        default = [i for i in self._last_status_items if i.path not in in_cl]
        groups: dict[str, list[PlasticItem]] = {"(default)": default, **grouped}
        for name, items in groups.items():
            if not items:
                continue
            hdr = [QStandardItem(name), QStandardItem(""), QStandardItem(""), QStandardItem("")]
            hdr[0].setFlags(Qt.ItemFlag.ItemIsEnabled)
            for plastic in sorted(items, key=lambda p: p.path.name):
                hdr[0].appendRow(self._make_file_row(plastic))
            self._status_model.appendRow(hdr)
        self._status_tree.expandAll()

    def _checked_items(self) -> list[PlasticItem]:
        result = []
        root = self._status_model.invisibleRootItem()
        for i in range(root.rowCount()):
            dir_item = root.child(i)
            for j in range(dir_item.rowCount()):
                file_item = dir_item.child(j)
                if file_item.checkState() == Qt.CheckState.Checked:
                    if plastic := file_item.data(Qt.ItemDataRole.UserRole):
                        result.append(plastic)
        return result

    # ── Drain (100ms QTimer → main thread) ───────────────────────────────────

    def _drain(self) -> None:
        for _ in range(self._DRAIN_LIMIT):
            try:
                kind, payload = self._queue.get_nowait()
            except queue.Empty:
                break
            match kind:
                case "status":
                    self._build_status_tree(payload)       # type: ignore[arg-type]
                case "changesets":
                    items: list[Changeset] = payload  # type: ignore[assignment]
                    self._changeset_model.reset(items)
                    from ._dag import BranchNode, build_cs_graph
                    branch_names = list(dict.fromkeys(cs.branch for cs in items))
                    nodes = [BranchNode(name=b, parent="") for b in branch_names]
                    self._graph_delegate.set_rows(build_cs_graph(items, nodes))
                case "branches":
                    self._branch_tree.reset(payload)       # type: ignore[arg-type]
                    self._branch_view.expandAll()
                case "labels":
                    self._label_model.reset(payload)       # type: ignore[arg-type]
                case "shelves":
                    self._shelve_model.reset(payload)      # type: ignore[arg-type]
                case "header":
                    branch, repo = payload  # type: ignore[misc]
                    self._apply_header(branch, repo)
                case "error":
                    sb = self.statusBar()
                    sb.setStyleSheet("QStatusBar { color: red; }")
                    sb.showMessage(str(payload), 8000)
                case "status_msg":
                    sb = self.statusBar()
                    sb.setStyleSheet("")
                    sb.showMessage(str(payload))
                case "diff":
                    text = str(payload)
                    if self._inline_diff_pending:
                        name = self._pending_diff_item.path.name if self._pending_diff_item else ""
                        self._pending_diff_panel.show_diff(text, name)
                        self._inline_diff_pending = False
                    else:
                        self._prev_page = self._stack.currentIndex()
                        self._diff_view.setPlainText(text)
                        self._stack.setCurrentIndex(self._diff_page_index)
                case "busy":
                    self._progress.setVisible(bool(payload))
                case "history":
                    path, revisions = payload   # type: ignore[misc]
                    HistoryDialog(path, revisions, self).show()
                case "blame":
                    path, lines = payload       # type: ignore[misc]
                    BlameDialog(path, lines, self).show()
                case "reviews":
                    self._review_model.reset(payload)      # type: ignore[arg-type]
                case "changelist_status":
                    self._last_changelist_status = payload  # type: ignore[assignment]
                    if self._group_mode == 2:
                        self._build_by_changelist(payload)  # type: ignore[arg-type]
                case "workspace_info":
                    self._apply_workspace_info(payload)     # type: ignore[arg-type]
                case "find_results":
                    self._show_find_results_dialog(payload)  # type: ignore[arg-type]
                case "xlinks":
                    self._xlink_model.reset(payload)         # type: ignore[arg-type]
                case "attributes":
                    obj_spec, items = payload                # type: ignore[misc]
                    AttributesDialog(obj_spec, items, self).show()
                case "acl":
                    _, items = payload                  # type: ignore[misc]
                    self._acl_model.reset(items)
                case "users":
                    self._user_model.reset(payload)          # type: ignore[arg-type]
                case "groups":
                    self._group_model.reset(payload)         # type: ignore[arg-type]
                case "dag":
                    nodes, branches = payload                # type: ignore[misc]
                    self._dag_widget.load(nodes, branches)
                case "merge_sides":
                    path, base, source, dest = payload       # type: ignore[misc]
                    ThreeWayMergeDialog(path, base, source, dest, self).show()
                case "config_entries":
                    self._config_model.reset(payload)        # type: ignore[arg-type]
                case "workspaces":
                    self._workspace_model.reset(payload)     # type: ignore[arg-type]
                case "repos":
                    self._repo_model.reset(payload)          # type: ignore[arg-type]
                case "triggers":
                    self._trigger_model.reset(payload)       # type: ignore[arg-type]
                case "cs_files":
                    self._cs_detail.load_files(payload)      # type: ignore[arg-type]

    # ── PlasticViewProtocol — called from any thread, enqueue only ───────────

    def set_status_items(self, items: list[PlasticItem]) -> None:
        self._queue.put(("status", items))

    def set_changesets(self, items: list[Changeset]) -> None:
        self._queue.put(("changesets", items))

    def set_branches(self, items: list[Branch]) -> None:
        self._queue.put(("branches", items))

    def set_labels(self, items: list[Label]) -> None:
        self._queue.put(("labels", items))

    def set_shelves(self, items: list[Shelve]) -> None:
        self._queue.put(("shelves", items))

    def set_header(self, branch: str, repo: str) -> None:
        self._queue.put(("header", (branch, repo)))

    def show_error(self, msg: str) -> None:
        self._queue.put(("error", msg))

    def show_diff(self, text: str) -> None:
        self._queue.put(("diff", text))

    def set_status_message(self, msg: str) -> None:
        self._queue.put(("status_msg", msg))

    def set_busy(self, busy: bool) -> None:
        self._queue.put(("busy", busy))

    def show_history(self, path: Path, items: list[Revision]) -> None:
        self._queue.put(("history", (path, items)))

    def show_blame(self, path: Path, items: list[BlameLine]) -> None:
        self._queue.put(("blame", (path, items)))

    def set_reviews(self, items: list[Review]) -> None:
        self._queue.put(("reviews", items))

    def set_changelist_status(self, grouped: dict[str, list[PlasticItem]]) -> None:
        self._queue.put(("changelist_status", grouped))

    def set_workspace_info(self, wi: object) -> None:
        self._queue.put(("workspace_info", wi))

    def show_find_results(self, paths: list[Path]) -> None:
        self._queue.put(("find_results", paths))

    def set_xlinks(self, items: list) -> None:
        self._queue.put(("xlinks", items))

    def show_attributes(self, obj_spec: str, items: list) -> None:
        self._queue.put(("attributes", (obj_spec, items)))

    def show_acl(self, obj_spec: str, items: list) -> None:
        self._queue.put(("acl", (obj_spec, items)))

    def set_users(self, items: list) -> None:
        self._queue.put(("users", items))

    def set_groups(self, items: list) -> None:
        self._queue.put(("groups", items))

    def set_dag(self, nodes: list, branches: list) -> None:
        self._queue.put(("dag", (nodes, branches)))

    def show_merge_sides(self, path: Path, base: str, source: str, dest: str) -> None:
        self._queue.put(("merge_sides", (path, base, source, dest)))

    def show_config_entries(self, items: list) -> None:
        self._queue.put(("config_entries", items))

    def set_workspaces(self, items: list) -> None:
        self._queue.put(("workspaces", items))

    def set_repos(self, items: list) -> None:
        self._queue.put(("repos", items))

    def set_triggers(self, items: list) -> None:
        self._queue.put(("triggers", items))

    def set_cs_files(self, files: list[CSDiffFile]) -> None:
        self._queue.put(("cs_files", files))

    def _apply_header(self, branch: str, repo: str) -> None:
        self._header_label.setText(f"Branch: {branch}   |   Repo: {repo}")
        self.setWindowTitle(f"Plastic SCM — {branch}")
        self._branch_tree.set_current(branch)

    def _apply_workspace_info(self, wi: WorkspaceInfo) -> None:
        parts = [f"Branch: {wi.branch}"] if wi.branch else ["Branch: —"]
        if wi.last_cs:
            parts.append(f"CS#{wi.last_cs}")
        if wi.server:
            parts.append(wi.server)
        self._header_label.setText("   |   ".join(parts))
        self.setWindowTitle(f"Plastic SCM — {wi.branch or wi.name}")
        self._branch_tree.set_current(wi.branch)
        self._wk_path = wi.wk_path

    def _on_find_files(self) -> None:
        pattern, ok = QInputDialog.getText(self, "Find Files", "Name pattern (e.g. *.py):")
        if ok and pattern.strip():
            self.find_files_requested.emit(pattern.strip())

    def _on_sbs_diff(self) -> None:
        SideBySideDiffDialog(self._diff_view.toPlainText(), self).show()

    def _on_add_xlink(self) -> None:
        path, ok = QInputDialog.getText(self, "Add Xlink", "Local mount path:")
        if not ok or not path.strip():
            return
        server, ok = QInputDialog.getText(self, "Add Xlink", "Server:")
        if not ok or not server.strip():
            return
        repo, ok = QInputDialog.getText(self, "Add Xlink", "Repository:")
        if not ok or not repo.strip():
            return
        self.add_xlink_requested.emit(path.strip(), server.strip(), repo.strip())

    def _on_remove_xlink(self) -> None:
        idx = self._xlink_table.currentIndex()
        if not idx.isValid():
            return
        source = idx.model().mapToSource(idx) if hasattr(idx.model(), "mapToSource") else idx
        if item := self._xlink_model.item_at(source.row()):
            self.remove_xlink_requested.emit(item.path)

    def _show_find_results_dialog(self, paths: list[Path]) -> None:
        from ._components import FindResultsDialog
        FindResultsDialog(paths, self).show()

    # ── Action handlers ───────────────────────────────────────────────────────

    def _selected_rows(self, table: QTableView) -> list[int]:
        return [idx.row() for idx in table.selectionModel().selectedRows()]

    def _selected_branch(self) -> Branch | None:
        idx = self._branch_view.currentIndex()
        if not idx.isValid():
            return None
        src = self._branch_proxy.mapToSource(idx)
        return self._branch_tree.branch_at(src)

    def _src_row(self, proxy: QSortFilterProxyModel, proxy_row: int) -> int:
        return proxy.mapToSource(proxy.index(proxy_row, 0)).row()

    def _on_checkin(self) -> None:
        items = self._checked_items()
        comment = self._comment_edit.text().strip()
        if not items or not comment:
            return
        self.checkin_requested.emit(items, comment)

    def _on_undo(self) -> None:
        if items := self._checked_items():
            self.undo_requested.emit(items)

    def _on_undo_keep(self) -> None:
        if items := self._checked_items():
            self.undo_keep_requested.emit(items)

    def _on_undo_changeset(self) -> None:
        rows = self._selected_rows(self._cs_table)
        if rows and (item := self._changeset_model.item_at(self._src_row(self._cs_proxy, rows[0]))):
            self.undo_changeset_requested.emit(item.cs_id)

    def _on_diff_file(self) -> None:
        indexes = self._status_tree.selectedIndexes()
        if not indexes:
            return
        item = self._status_model.itemFromIndex(indexes[0])
        if item and (plastic := item.data(Qt.ItemDataRole.UserRole)):
            self.diff_file_requested.emit(plastic)

    def _on_cs_double_click(self, index: QModelIndex) -> None:
        src = self._cs_proxy.mapToSource(index)
        if item := self._changeset_model.item_at(src.row()):
            self.cs_double_clicked.emit(item.cs_id)

    def _on_switch_cs(self) -> None:
        rows = self._selected_rows(self._cs_table)
        if rows and (item := self._changeset_model.item_at(self._src_row(self._cs_proxy, rows[0]))):
            self.switch_to_cs.emit(item.cs_id)

    def _on_diff_prev(self) -> None:
        rows = self._selected_rows(self._cs_table)
        if rows and (item := self._changeset_model.item_at(self._src_row(self._cs_proxy, rows[0]))):
            self.diff_with_prev.emit(item.cs_id)

    def _on_switch_branch(self) -> None:
        if item := self._selected_branch():
            self.switch_branch.emit(item.name)

    def _on_create_branch(self) -> None:
        name, ok = QInputDialog.getText(self, "Create Branch", "Branch name:")
        if ok and name.strip():
            self.create_branch_requested.emit(name.strip())

    def _on_switch_label(self) -> None:
        rows = self._selected_rows(self._label_table)
        if rows and (item := self._label_model.item_at(self._src_row(self._label_proxy, rows[0]))):
            self.switch_to_label.emit(item.name)

    def _on_shelve(self) -> None:
        items = self._checked_items()
        comment = self._comment_edit.text().strip()
        if not items or not comment:
            return
        self.shelve_requested.emit(items, comment)

    def _on_unshelve(self) -> None:
        rows = self._selected_rows(self._shelve_table)
        if rows and (item := self._shelve_model.item_at(self._src_row(self._shelve_proxy, rows[0]))):
            self.unshelve_requested.emit(item.shelve_id)

    def _on_rollback_cs(self) -> None:
        rows = self._selected_rows(self._cs_table)
        if rows and (item := self._changeset_model.item_at(self._src_row(self._cs_proxy, rows[0]))):
            self.rollback_cs_requested.emit(item.cs_id)

    def _on_merge_branch(self) -> None:
        item = self._selected_branch()
        if not item:
            return
        from ._components import MergeOptionsDialog
        dlg = MergeOptionsDialog(self)
        if dlg.exec():
            preview, _cherrypick, resolve, semantic = dlg.get_options()
            self.merge_branch_requested.emit(item.name, preview, resolve, semantic)

    def _on_lock(self) -> None:
        if items := self._checked_items():
            self.lock_requested.emit(items)

    def _on_unlock(self) -> None:
        if items := self._checked_items():
            self.unlock_requested.emit(items)

    def _on_view_history(self) -> None:
        indexes = self._status_tree.selectedIndexes()
        if not indexes:
            return
        item = self._status_model.itemFromIndex(indexes[0])
        if item and (plastic := item.data(Qt.ItemDataRole.UserRole)):
            self.history_requested.emit(plastic)

    def _on_blame(self) -> None:
        indexes = self._status_tree.selectedIndexes()
        if not indexes:
            return
        item = self._status_model.itemFromIndex(indexes[0])
        if item and (plastic := item.data(Qt.ItemDataRole.UserRole)):
            self.blame_requested.emit(plastic)

    def _on_merge_view(self) -> None:
        indexes = self._status_tree.selectedIndexes()
        if not indexes:
            return
        item = self._status_model.itemFromIndex(indexes[0])
        if item and (plastic := item.data(Qt.ItemDataRole.UserRole)):
            self.merge_view_requested.emit(plastic)

    def _on_create_label(self) -> None:
        name, ok = QInputDialog.getText(self, "Create Label", "Label name:")
        if not ok or not name.strip():
            return
        cs_id, ok = QInputDialog.getInt(self, "Create Label", "Changeset ID:", min=0)
        if ok:
            self.create_label_requested.emit(name.strip(), cs_id)

    def _on_delete_label(self) -> None:
        rows = self._selected_rows(self._label_table)
        if rows and (item := self._label_model.item_at(self._src_row(self._label_proxy, rows[0]))):
            self.delete_label_requested.emit(item.name)

    def _on_rename_label(self) -> None:
        rows = self._selected_rows(self._label_table)
        if not rows:
            return
        item = self._label_model.item_at(self._src_row(self._label_proxy, rows[0]))
        if not item:
            return
        new_name, ok = QInputDialog.getText(self, "Rename Label", "New name:", text=item.name)
        if ok and new_name.strip():
            self.rename_label_requested.emit(item.name, new_name.strip())

    def _on_delete_branch(self) -> None:
        if item := self._selected_branch():
            self.delete_branch_requested.emit(item.name)

    def _on_move_to_changelist(self) -> None:
        items = self._checked_items()
        if not items:
            return
        name, ok = QInputDialog.getText(self, "Move to Changelist", "Changelist name:")
        if ok and name.strip():
            self.move_to_changelist_requested.emit(items, name.strip())

    def _on_create_review(self) -> None:
        cs_id, ok = QInputDialog.getInt(self, "Create Review", "Target CS ID:", min=0)
        if not ok:
            return
        title, ok = QInputDialog.getText(self, "Create Review", "Title:")
        if not ok or not title.strip():
            return
        assignee, _ = QInputDialog.getText(self, "Create Review", "Assignee (optional):")
        self.create_review_requested.emit(cs_id, title.strip(), assignee.strip())

    def _on_edit_review_status(self) -> None:
        rows = self._selected_rows(self._review_table)
        if not rows:
            return
        r = self._review_model.item_at(self._src_row(self._review_proxy, rows[0]))
        if not r:
            return
        status, ok = QInputDialog.getItem(
            self, "Edit Status", "New status:", list(REVIEW_STATUSES), editable=False
        )
        if ok:
            self.edit_review_requested.emit(r.review_id, status)

    def _on_delete_review(self) -> None:
        rows = self._selected_rows(self._review_table)
        if rows and (r := self._review_model.item_at(self._src_row(self._review_proxy, rows[0]))):
            self.delete_review_requested.emit(r.review_id)

    def _on_rename_branch(self) -> None:
        item = self._selected_branch()
        if not item:
            return
        new_name, ok = QInputDialog.getText(self, "Rename Branch", "New name:", text=item.name)
        if ok and new_name.strip():
            self.rename_branch_requested.emit(item.name, new_name.strip())

    # ── File ops handlers (4.7) ───────────────────────────────────────────────

    def _on_add_to_vcs(self) -> None:
        if items := self._checked_items():
            self.add_to_vcs_requested.emit(items)

    def _on_remove_from_vcs(self) -> None:
        if items := self._checked_items():
            self.remove_from_vcs_requested.emit(items)

    def _on_move_file(self) -> None:
        indexes = self._status_tree.selectedIndexes()
        if not indexes:
            return
        item = self._status_model.itemFromIndex(indexes[0])
        if not (item and (plastic := item.data(Qt.ItemDataRole.UserRole))):
            return
        dst_str, ok = QInputDialog.getText(
            self, "Move/Rename", "Destination path:", text=str(plastic.path)
        )
        if ok and dst_str.strip():
            self.move_file_requested.emit(plastic.path, Path(dst_str.strip()))

    # ── Advanced diff handlers (4.8) ──────────────────────────────────────────

    def _on_diff_cs_range(self) -> None:
        rows = self._selected_rows(self._cs_table)
        if not rows:
            return
        item = self._changeset_model.item_at(self._src_row(self._cs_proxy, rows[0]))
        if not item:
            return
        cs_b, ok = QInputDialog.getInt(self, "Diff CS Range", "Compare with CS ID:", value=item.cs_id)
        if ok:
            self.diff_cs_range_requested.emit(item.cs_id, cs_b)

    def _on_diff_branch(self) -> None:
        if item := self._selected_branch():
            self.diff_branch_requested.emit(item.name)

    def _on_view_branch_in_dag(self) -> None:
        self._stack.setCurrentIndex(8)
        self._nav.setCurrentRow(8)
        self.refresh_dag.emit()

    def _on_diff_labels(self) -> None:
        rows = self._selected_rows(self._label_table)
        if not rows:
            return
        item = self._label_model.item_at(self._src_row(self._label_proxy, rows[0]))
        if not item:
            return
        lb_b, ok = QInputDialog.getText(self, "Diff Labels", "Compare with label:", text=item.name)
        if ok and lb_b.strip():
            self.diff_labels_requested.emit(item.name, lb_b.strip())

    def _on_diff_shelve(self) -> None:
        rows = self._selected_rows(self._shelve_table)
        if rows and (item := self._shelve_model.item_at(self._src_row(self._shelve_proxy, rows[0]))):
            self.diff_shelve_requested.emit(item.shelve_id)

    # ── Admin page handlers (5.8) ─────────────────────────────────────────────

    def _on_add_user(self) -> None:
        name, ok = QInputDialog.getText(self, "Add User", "Username:")
        if not ok or not name.strip():
            return
        email, _ = QInputDialog.getText(self, "Add User", "Email (optional):")
        self.add_user_requested.emit(name.strip(), email.strip())

    def _on_delete_user(self) -> None:
        rows = self._selected_rows(self._user_table)
        if rows and (item := self._user_model.item_at(self._src_row(self._user_proxy, rows[0]))):
            self.delete_user_requested.emit(item.name)

    def _on_add_group(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Group", "Group name:")
        if ok and name.strip():
            self.add_group_requested.emit(name.strip())

    def _on_delete_group(self) -> None:
        rows = self._selected_rows(self._group_table)
        if rows and (item := self._group_model.item_at(self._src_row(self._group_proxy, rows[0]))):
            self.delete_group_requested.emit(item.name)

    def _on_load_acl(self) -> None:
        spec = self._acl_spec_edit.text().strip()
        if spec:
            self.load_acl_requested.emit(spec)

    def _on_set_acl(self) -> None:
        spec = self._acl_spec_edit.text().strip()
        if not spec:
            return
        principal, ok = QInputDialog.getText(self, "Set ACL", "Principal (user/group):")
        if not ok or not principal.strip():
            return
        perm, ok = QInputDialog.getText(self, "Set ACL", "Permission (Read/Write/ReadWrite/None):")
        if not ok or not perm.strip():
            return
        self.set_acl_requested.emit(spec, principal.strip(), perm.strip())

    def _on_delete_acl(self) -> None:
        spec = self._acl_spec_edit.text().strip()
        if not spec:
            return
        rows = self._selected_rows(self._acl_table)
        if rows and (item := self._acl_model.item_at(self._src_row(self._acl_proxy, rows[0]))):
            self.delete_acl_requested.emit(spec, item.principal)

    def _on_add_group_member(self) -> None:
        rows = self._selected_rows(self._group_table)
        if not rows:
            return
        grp = self._group_model.item_at(self._src_row(self._group_proxy, rows[0]))
        if not grp:
            return
        user, ok = QInputDialog.getText(self, "Add Member", f"Add user to '{grp.name}':")
        if ok and user.strip():
            self.add_group_member_requested.emit(grp.name, user.strip())

    # ── Package replication handlers (#9) ─────────────────────────────────────

    def _on_pkg_create(self) -> None:
        path = self._pkg_path_edit.text().strip()
        if path:
            self.replica_pkg_create_requested.emit(path)

    def _on_pkg_import(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Import Package", "", "Replication packages (*.rep);;All files (*)")
        if path:
            self.replica_pkg_import_requested.emit(path)

    # ── Workspace config file handlers (#2 / #3) ──────────────────────────────

    def _on_edit_ignore(self) -> None:
        if self._wk_path is None:
            return
        path = ignore_conf_path(self._wk_path)
        dlg = ConfEditorDialog("Edit ignore.conf", path, self)
        if dlg.exec():
            write_conf(path, dlg.text())

    def _on_edit_cloaked(self) -> None:
        if self._wk_path is None:
            return
        path = cloaked_conf_path(self._wk_path)
        dlg = ConfEditorDialog("Edit cloaked.conf", path, self)
        if dlg.exec():
            write_conf(path, dlg.text())

    # ── Preferences handlers (#8) ─────────────────────────────────────────────

    def _on_set_config(self) -> None:
        rows = self._selected_rows(self._config_table)
        if rows and (entry := self._config_model.item_at(self._src_row(self._config_proxy, rows[0]))):
            key = entry.key
        else:
            key, ok = QInputDialog.getText(self, "Set Config", "Key:")
            if not ok or not key.strip():
                return
            key = key.strip()
        value, ok = QInputDialog.getText(self, "Set Config", f"Value for '{key}':")
        if ok and value.strip():
            self.set_config_requested.emit(key, value.strip())

    # ── Partial workspace handlers (#5) ───────────────────────────────────────

    def _on_partial_add(self) -> None:
        path, ok = QInputDialog.getText(self, "Add Partial Path", "Path to include:")
        if ok and path.strip():
            self.add_partial_requested.emit(path.strip())

    def _on_partial_remove(self) -> None:
        path, ok = QInputDialog.getText(self, "Remove Partial Path", "Path to exclude:")
        if ok and path.strip():
            self.remove_partial_requested.emit(path.strip())

    # ── Workspace & Repo CRUD handlers (#1) ──────────────────────────────────

    def _on_create_workspace(self) -> None:
        name, ok = QInputDialog.getText(self, "Create Workspace", "Name:")
        if not ok or not name.strip():
            return
        path, ok = QInputDialog.getText(self, "Create Workspace", "Local path:")
        if not ok or not path.strip():
            return
        server, ok = QInputDialog.getText(self, "Create Workspace", "Server:")
        if not ok or not server.strip():
            return
        repo, ok = QInputDialog.getText(self, "Create Workspace", "Repository:")
        if not ok or not repo.strip():
            return
        self.create_workspace_requested.emit(name.strip(), path.strip(), server.strip(), repo.strip())

    def _on_delete_workspace(self) -> None:
        rows = self._selected_rows(self._wk_entry_table)
        if rows and (item := self._workspace_model.item_at(self._src_row(self._wk_entry_proxy, rows[0]))):
            self.delete_workspace_requested.emit(item.name)

    def _on_create_repo(self) -> None:
        name, ok = QInputDialog.getText(self, "Create Repository", "Name:")
        if ok and name.strip():
            self.create_repo_requested.emit(name.strip())

    def _on_delete_repo(self) -> None:
        rows = self._selected_rows(self._repo_table)
        if rows and (item := self._repo_model.item_at(self._src_row(self._repo_proxy, rows[0]))):
            self.delete_repo_requested.emit(item.name)

    # ── Trigger CRUD handlers (#6) ────────────────────────────────────────────

    def _on_create_trigger(self) -> None:
        name, ok = QInputDialog.getText(self, "Create Trigger", "Name:")
        if not ok or not name.strip():
            return
        event, ok = QInputDialog.getText(self, "Create Trigger", "Event (e.g. after-checkin):")
        if not ok or not event.strip():
            return
        filter_, ok = QInputDialog.getText(self, "Create Trigger", "Filter (e.g. *.py):")
        if not ok or not filter_.strip():
            return
        command, ok = QInputDialog.getText(self, "Create Trigger", "Command:")
        if not ok or not command.strip():
            return
        self.create_trigger_requested.emit(name.strip(), event.strip(), filter_.strip(), command.strip())

    def _on_delete_trigger(self) -> None:
        rows = self._selected_rows(self._trigger_table)
        if rows and (item := self._trigger_model.item_at(self._src_row(self._trigger_proxy, rows[0]))):
            self.delete_trigger_requested.emit(item.trigger_id)

    # ── Git Sync handlers (#4) ────────────────────────────────────────────────

    def _on_sync_git(self) -> None:
        url = self._git_url_edit.text().strip()
        if url:
            self.sync_git_requested.emit(url)

    # ── CS edit comment handler (4.10) ────────────────────────────────────────

    def _on_edit_cs_comment(self) -> None:
        rows = self._selected_rows(self._cs_table)
        if not rows:
            return
        item = self._changeset_model.item_at(self._src_row(self._cs_proxy, rows[0]))
        if not item:
            return
        new_comment, ok = QInputDialog.getText(
            self, "Edit Comment", "New comment:", text=item.comment
        )
        if ok and new_comment.strip():
            self.edit_cs_comment_requested.emit(item.cs_id, new_comment.strip())
