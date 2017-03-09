# -*- coding:utf-8 -*-
import unittest
from app import create_app, db
from app.models.post import Post


class PostApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


if __name__ == "__main__":
    unittest.main()
