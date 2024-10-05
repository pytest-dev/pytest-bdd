from functools import partial
from itertools import islice
from operator import attrgetter
from typing import TYPE_CHECKING, Optional

from pytest_bdd.utils import compose

if TYPE_CHECKING:  # pragma: no cover
    from cucumber_messages import DataTable


def data_table_to_dicts(data_table: Optional["DataTable"]):
    if data_table is None:
        return {}

    data_table_keys = map(attrgetter("value"), map(compose(next, iter), map(attrgetter("cells"), data_table.rows)))
    data_table_values = map(
        compose(list, compose(partial(map, attrgetter("value")), lambda items: islice(items, 1, None), iter)),
        map(attrgetter("cells"), data_table.rows),
    )
    return dict(zip(data_table_keys, data_table_values))
