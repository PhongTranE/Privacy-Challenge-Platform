
from src.constants.pagination import *
from flask_sqlalchemy.pagination import Pagination
import sqlalchemy as sa
import typing as t
from src.extensions import db

class PageNumberPagination:
    def __init__(
        self, 
        select: sa.sql.Select[t.Any], 
        page: int = None, 
        per_page: int = None, 
        error_out: bool = False, 
        count: bool = None
    ):
        """
        :param select: The SQLAlchemy select object.
        :param page: The current page number.
        :param per_page: Number of items per page.
        :param error_out: 404 or empty list.
        :param count: Whether to perform a count query to get the total number of items.
        """
        self.select = select
        self.page = page if page is not None else DEFAULT_PAGE
        self.per_page = min(per_page, MAX_PER_PAGE) if per_page is not None else DEFAULT_PER_PAGE
        self.error_out = error_out
        self.count = count if count is not None else True

    def paginate(self):
        if self.count:
            return self._with_count()
        else:
            return self._without_count()

    def _with_count(self):
        pagination: Pagination = db.paginate(
            select=self.select,
            page=self.page,
            per_page=self.per_page,
            error_out=self.error_out
        )
        return {
            'data': pagination.items,
            'meta': {
                'total_items': pagination.total,
                'total_pages': pagination.pages,
                'current_page': pagination.page,
                'per_page': pagination.per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }


    def _without_count(self):
        # Execute the select statement with limit and offset
        stmt = self.select.limit(self.per_page + 1).offset((self.page - 1) * self.per_page)
        result = db.session.execute(stmt)
        items = result.scalars().all()
        
        # Determine if there's a next page
        has_next = len(items) > self.per_page
        if has_next:
            items = items[:-1]  # Remove the extra item
        
        return {
            'data': items,
            'meta': {
                'total_items': None,
                'total_pages': None,
                'current_page': self.page,
                'per_page': self.per_page,
                'has_next': has_next,
                'has_prev': self.page > 1
            }
        }

