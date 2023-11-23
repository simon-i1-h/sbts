import datetime
import random
import string
import uuid

from django.db import DataError
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist, \
    ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .templatetags.pretty_filters import pretty_nbytes
from .views import TicketPageView, CreateTicketView, TicketDetailPageView, \
    CreateCommentView, FilePageView, CreateFileView, TopPageView
from sbts.ticket.models import Ticket, Comment
from sbts.file.models import UploadedFile, S3Uploader


class PrettyNbytesTest(TestCase):
    def test_pretty_nbytes_0(self):
        self.assertEqual(pretty_nbytes(0), '0 B')

    def test_pretty_nbytes_1(self):
        self.assertEqual(pretty_nbytes(1), '1 B')

    def test_pretty_nbytes_2(self):
        self.assertEqual(pretty_nbytes(2), '2 B')

    def test_pretty_nbytes_1023(self):
        '''
        1023までは単位が大きくならない。
        '''

        self.assertEqual(pretty_nbytes(1023), '1,023 B')

    def test_pretty_nbytes_1kib(self):
        '''
        1024の位ごとに単位が大きくなる。
        '''

        self.assertEqual(pretty_nbytes(1024), '1 kiB')

    def test_pretty_nbytes_fraction(self):
        '''
        端数は小数第1位まで有効。
        '''

        self.assertEqual(pretty_nbytes(1134), '1.1 kiB')

    def test_pretty_nbytes_fraction_rounddown(self):
        '''
        端数が出て、かつ小数第1位が0になる場合は省略。
        '''

        self.assertEqual(pretty_nbytes(1034), '1 kiB')

    def test_pretty_nbytes_kib_complex(self):
        '''
        複合: 桁上がり、2以上、端数
        '''

        self.assertEqual(pretty_nbytes(2600), '2.5 kiB')

    def test_pretty_nbytes_1023kib(self):
        '''
        1023までは単位が大きくならない。
        '''

        self.assertEqual(pretty_nbytes(1023 * 1024), '1,023 kiB')

    def test_pretty_nbytes_1mib(self):
        '''
        単位: k->M
        '''

        self.assertEqual(pretty_nbytes(1024 ** 2), '1 MiB')

    def test_pretty_nbytes_1023mib(self):
        '''
        1023までは単位が大きくならない。
        '''

        self.assertEqual(pretty_nbytes(1023 * (1024 ** 2)), '1,023 MiB')

    def test_pretty_nbytes_1gib(self):
        '''
        単位: M->G
        '''

        self.assertEqual(pretty_nbytes(1024 ** 3), '1 GiB')

    def test_pretty_nbytes_1023gib(self):
        '''
        1023までは単位が大きくならない。
        '''

        self.assertEqual(pretty_nbytes(1023 * (1024 ** 3)), '1,023 GiB')

    def test_pretty_nbytes_1tib(self):
        '''
        単位: G->T
        '''

        self.assertEqual(pretty_nbytes(1024 ** 4), '1 TiB')

    def test_pretty_nbytes_1023tib(self):
        '''
        1023までは単位が大きくならない。
        '''

        self.assertEqual(pretty_nbytes(1023 * (1024 ** 4)), '1,023 TiB')

    def test_pretty_nbytes_1pib(self):
        '''
        単位: T->P
        '''

        self.assertEqual(pretty_nbytes(1024 ** 5), '1 PiB')

    def test_pretty_nbytes_1023pib(self):
        '''
        1023までは単位が大きくならない。
        '''

        self.assertEqual(pretty_nbytes(1023 * (1024 ** 5)), '1,023 PiB')

    def test_pretty_nbytes_1024pib(self):
        '''
        単位はPで最大なので、それ以上は単に数が大きくなる。
        '''

        self.assertEqual(pretty_nbytes(1024 ** 6), '1,024 PiB')

    def test_pretty_nbytes_large_pib_complex(self):
        '''
        複合: 1024以上のPiB、端数
        '''

        self.assertEqual(pretty_nbytes(42 * (1024 ** 6) + 900 * (1024 ** 4)), '43,008.9 PiB')


class TicketPageViewTest(TestCase):
    '''
    チケットが期待通りの順序で一覧表示されることを確認する。
    '''

    def setUp(self):
        super().setUp()
        self.req_factory = RequestFactory()

    def test_empty(self):
        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [])
        self.assertEqual(resp.status_code, 200)

    def test_one(self):
        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='a', created_at=t1_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t1])
        self.assertEqual(resp.status_code, 200)

    def test_two(self):
        '''
        チケットの一覧はチケットの作成日時の降順になる。
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='b', created_at=t1_dt)
        t2_dt = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='a', created_at=t2_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t2, t1])
        self.assertEqual(resp.status_code, 200)

    def test_three(self):
        '''
        チケットの一覧はチケットの作成日時の降順になる。
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='c', created_at=t1_dt)
        t2_dt = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='b', created_at=t2_dt)
        t3_dt = datetime.datetime.fromisoformat('2023-10-24T03:15:00Z')
        t3 = Ticket.objects.create(title='a', created_at=t3_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t2, t3, t1])
        self.assertEqual(resp.status_code, 200)

    def test_comment_one(self):
        '''
        チケットにコメントがあっても、チケットの一覧はチケットの作成日
        時の降順になる。

        最終変更日は、コメントがあれば最新コメント日時に、なければチケッ
        トの作成日になる。
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='c', created_at=t1_dt)
        t1_c1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:15Z')
        t1.comment_set.create(comment='a', created_at=t1_c1_dt)

        t2_dt = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='b', created_at=t2_dt)
        # 何故かチケット作成日よりコメント日の方が早いが、許容する
        t2_c1_dt = datetime.datetime.fromisoformat('2023-10-22T11:00:30Z')
        t2.comment_set.create(comment='b', created_at=t2_c1_dt)

        t3_dt = datetime.datetime.fromisoformat('2023-10-24T03:15:00Z')
        t3 = Ticket.objects.create(title='a', created_at=t3_dt)
        t3_c1_dt = datetime.datetime.fromisoformat('2023-10-24T23:00:30Z')
        t3.comment_set.create(comment='c', created_at=t3_c1_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t2, t3, t1])
        self.assertEqual(resp.context_data['ticket_list'][0].lastmod, t2_c1_dt)
        self.assertEqual(resp.context_data['ticket_list'][1].lastmod, t3_c1_dt)
        self.assertEqual(resp.context_data['ticket_list'][2].lastmod, t1_c1_dt)
        self.assertEqual(resp.status_code, 200)

    def test_comment_two(self):
        '''
        チケットにコメントがあっても、チケットの一覧はチケットの作成日
        時の降順になる。

        最終変更日は、コメントがあれば最新コメント日時に、なければチケッ
        トの作成日になる。
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='c', created_at=t1_dt)
        t1_c1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:30Z')
        t1.comment_set.create(comment='a', created_at=t1_c1_dt)
        t1_c2_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:15Z')
        t1.comment_set.create(comment='b', created_at=t1_c2_dt)

        t2_dt = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='b', created_at=t2_dt)
        # 何故かチケット作成日よりコメント日の方が早いが、許容する
        t2_c1_dt = datetime.datetime.fromisoformat('2023-10-22T11:00:15Z')
        t2.comment_set.create(comment='c', created_at=t2_c1_dt)
        t2_c2_dt = datetime.datetime.fromisoformat('2023-10-22T11:00:30Z')
        t2.comment_set.create(comment='d', created_at=t2_c2_dt)

        t3_dt = datetime.datetime.fromisoformat('2023-10-24T03:15:00Z')
        t3 = Ticket.objects.create(title='a', created_at=t3_dt)
        t3_c1_dt = datetime.datetime.fromisoformat('2023-10-24T23:05:00Z')
        t3.comment_set.create(comment='e', created_at=t3_c1_dt)
        t3_c2_dt = datetime.datetime.fromisoformat('2023-10-24T23:00:00Z')
        t3.comment_set.create(comment='f', created_at=t3_c2_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t2, t3, t1])
        self.assertEqual(resp.context_data['ticket_list'][0].lastmod, t2_c2_dt)
        self.assertEqual(resp.context_data['ticket_list'][1].lastmod, t3_c1_dt)
        self.assertEqual(resp.context_data['ticket_list'][2].lastmod, t1_c1_dt)
        self.assertEqual(resp.status_code, 200)

    def test_comment_three(self):
        '''
        チケットにコメントがあっても、チケットの一覧はチケットの作成日
        時の降順になる。

        最終変更日は、コメントがあれば最新コメント日時に、なければチケッ
        トの作成日になる。
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='c', created_at=t1_dt)
        t1_c1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:30Z')
        t1.comment_set.create(comment='a', created_at=t1_c1_dt)
        t1_c2_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:15Z')
        t1.comment_set.create(comment='b', created_at=t1_c2_dt)
        t1_c3_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:40Z')
        t1.comment_set.create(comment='c', created_at=t1_c3_dt)

        t2_dt = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='b', created_at=t2_dt)
        # 何故かチケット作成日よりコメント日の方が早いが、許容する
        t2_c1_dt = datetime.datetime.fromisoformat('2023-10-22T11:01:00Z')
        t2.comment_set.create(comment='d', created_at=t2_c1_dt)
        t2_c2_dt = datetime.datetime.fromisoformat('2023-10-22T11:00:30Z')
        t2.comment_set.create(comment='e', created_at=t2_c2_dt)
        t2_c3_dt = datetime.datetime.fromisoformat('2023-10-22T11:00:00Z')
        t2.comment_set.create(comment='f', created_at=t2_c3_dt)

        t3_dt = datetime.datetime.fromisoformat('2023-10-24T03:15:00Z')
        t3 = Ticket.objects.create(title='a', created_at=t3_dt)
        t3_c1_dt = datetime.datetime.fromisoformat('2023-10-24T23:00:00Z')
        t3.comment_set.create(comment='g', created_at=t3_c1_dt)
        t3_c2_dt = datetime.datetime.fromisoformat('2023-10-25T01:00:00Z')
        t3.comment_set.create(comment='h', created_at=t3_c2_dt)
        t3_c3_dt = datetime.datetime.fromisoformat('2023-10-24T23:00:10Z')
        t3.comment_set.create(comment='i', created_at=t3_c3_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t2, t3, t1])
        self.assertEqual(resp.context_data['ticket_list'][0].lastmod, t2_c1_dt)
        self.assertEqual(resp.context_data['ticket_list'][1].lastmod, t3_c2_dt)
        self.assertEqual(resp.context_data['ticket_list'][2].lastmod, t1_c3_dt)
        self.assertEqual(resp.status_code, 200)

    def test_ticket_and_comment(self):
        '''
        チケットにコメントがあっても、チケットの一覧はチケットの作成日
        時の降順になる。

        最終変更日は、コメントがあれば最新コメント日時に、なければチケッ
        トの作成日になる。
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='c', created_at=t1_dt)
        t1_c1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:15Z')
        t1.comment_set.create(comment='a', created_at=t1_c1_dt)

        t2_dt = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='b', created_at=t2_dt)

        t3_dt = datetime.datetime.fromisoformat('2023-10-24T03:15:00Z')
        t3 = Ticket.objects.create(title='a', created_at=t3_dt)
        t3_c1_dt = datetime.datetime.fromisoformat('2023-10-24T23:00:30Z')
        t3.comment_set.create(comment='d', created_at=t3_c1_dt)
        t3_c2_dt = datetime.datetime.fromisoformat('2023-10-25T05:00:30Z')
        t3.comment_set.create(comment='c', created_at=t3_c2_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t2, t3, t1])
        self.assertEqual(resp.context_data['ticket_list'][0].lastmod, t2_dt)
        self.assertEqual(resp.context_data['ticket_list'][1].lastmod, t3_c2_dt)
        self.assertEqual(resp.context_data['ticket_list'][2].lastmod, t1_c1_dt)
        self.assertEqual(resp.status_code, 200)

    def test_options(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.options('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertEqual(resp.status_code, 200)

    def test_head(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.head('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertEqual(resp.status_code, 200)

    def test_post(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.post('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_put(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.put('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_patch(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.patch('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_delete(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.delete('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_trace(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.trace('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)


class CreateTicketViewTest(TestCase):
    '''
    チケットを期待通り作れるか確認する。各期待しないパラメータについて
    は、他のすべてのパラメータは期待の値にして検証する。
    '''

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_shimon = User.objects.create_user(
            'shimon', 'shimon@example.com', 'pw')

    def setUp(self):
        super().setUp()
        self.req_factory = RequestFactory()

    def test_anon(self):
        '''
        未ログインはチケット作成不可
        '''

        self.assertQuerySetEqual(Ticket.objects.all(), [])

        req = self.req_factory.post('/', data={'title': 't1'})
        req.user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            CreateTicketView.as_view()(req)
        self.assertQuerySetEqual(Ticket.objects.all(), [])

    def test_ok(self):
        self.assertQuerySetEqual(Ticket.objects.all(), [])

        t1_title = 't1'
        req = self.req_factory.post('/', data={'title': t1_title})
        req.user = self.user_shimon

        resp = CreateTicketView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('page:ticket_page'))
        self.assertQuerySetEqual(Ticket.objects.all(), [Ticket.objects.get(title=t1_title)])

    def test_extra_data(self):
        '''
        POSTで余計なデータが来た場合は余計なデータを無視して成功
        '''

        self.assertQuerySetEqual(Ticket.objects.all(), [])

        t1_title = 't1'
        req = self.req_factory.post('/', data={'title': t1_title, 'extra': 'extra'})
        req.user = self.user_shimon

        resp = CreateTicketView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('page:ticket_page'))
        self.assertQuerySetEqual(Ticket.objects.all(), [Ticket.objects.get(title=t1_title)])

    def test_empty_title(self):
        '''
        タイトルが空文字列の場合は成功
        '''

        self.assertQuerySetEqual(Ticket.objects.all(), [])

        t1_title = ''
        req = self.req_factory.post('/', data={'title': t1_title})
        req.user = self.user_shimon
        resp = CreateTicketView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('page:ticket_page'))
        self.assertQuerySetEqual(Ticket.objects.all(), [Ticket.objects.get(title=t1_title)])

    def test_too_long_title(self):
        '''
        タイトルがすごく長い場合は成功
        '''

        self.assertQuerySetEqual(Ticket.objects.all(), [])

        t1_title = 't' * 1024
        req = self.req_factory.post('/', data={'title': t1_title})
        req.user = self.user_shimon
        resp = CreateTicketView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('page:ticket_page'))
        self.assertQuerySetEqual(Ticket.objects.all(), [Ticket.objects.get(title=t1_title)])

    def test_no_title(self):
        '''
        タイトルがない場合は例外を送出
        '''

        self.assertQuerySetEqual(Ticket.objects.all(), [])

        req = self.req_factory.post('/', data={})
        req.user = self.user_shimon

        with self.assertRaises(Exception):
            CreateTicketView.as_view()(req)
        self.assertQuerySetEqual(Ticket.objects.all(), [])

    def test_options(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.options('/')
        req.user = self.user_shimon
        resp = CreateTicketView.as_view()(req)
        self.assertEqual(resp.status_code, 200)

    def test_head(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.head('/')
        req.user = self.user_shimon
        resp = CreateTicketView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_get(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.get('/')
        req.user = self.user_shimon
        resp = CreateTicketView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_put(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.put('/')
        req.user = self.user_shimon
        resp = CreateTicketView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_patch(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.patch('/')
        req.user = self.user_shimon
        resp = CreateTicketView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_delete(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.delete('/')
        req.user = self.user_shimon
        resp = CreateTicketView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_trace(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.trace('/')
        req.user = self.user_shimon
        resp = CreateTicketView.as_view()(req)
        self.assertEqual(resp.status_code, 405)


class TicketDetailPageViewTest(TestCase):
    '''
    チケットの詳細が期待通りの順序で一覧表示されることを確認する。
    '''

    def setUp(self):
        super().setUp()
        self.req_factory = RequestFactory()

    def test_invalid_ticket(self):
        '''
        指定したチケットが存在しなければ例外を送出
        '''

        key = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d5d')
        self.assertQuerySetEqual(Ticket.objects.all(), [])

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        with self.assertRaises(ObjectDoesNotExist):
            TicketDetailPageView.as_view()(req, key=key)

    def test_empty(self):
        dt1 = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertQuerySetEqual(resp.context_data['comment_list'], [])
        self.assertEqual(resp.status_code, 200)

    def test_one(self):
        t1_dt = datetime.datetime.fromisoformat('2023-10-22T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)

        t1_c1_dt = datetime.datetime.fromisoformat('2023-10-26T15:00:00Z')
        t1_c1 = t1.comment_set.create(comment='a', created_at=t1_c1_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.context_data['ticket'], t1)
        self.assertQuerySetEqual(resp.context_data['comment_list'], [t1_c1])
        self.assertEqual(resp.status_code, 200)

    def test_two(self):
        '''
        コメントの一覧はコメントの作成日時の昇順になる。
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-22T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)

        t1_c1_dt = datetime.datetime.fromisoformat('2023-10-26T20:00:00Z')
        t1_c1 = t1.comment_set.create(comment='a', created_at=t1_c1_dt)
        t1_c2_dt = datetime.datetime.fromisoformat('2023-10-26T15:00:00Z')
        t1_c2 = t1.comment_set.create(comment='b', created_at=t1_c2_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.context_data['ticket'], t1)
        self.assertQuerySetEqual(resp.context_data['comment_list'], [t1_c2, t1_c1])
        self.assertEqual(resp.status_code, 200)

    def test_three(self):
        '''
        コメントの一覧はコメントの作成日時の昇順になる。
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-22T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)

        t1_c1_dt = datetime.datetime.fromisoformat('2023-10-26T20:00:00Z')
        t1_c1 = t1.comment_set.create(comment='a', created_at=t1_c1_dt)
        t1_c2_dt = datetime.datetime.fromisoformat('2023-10-26T09:00:00Z')
        t1_c2 = t1.comment_set.create(comment='b', created_at=t1_c2_dt)
        t1_c3_dt = datetime.datetime.fromisoformat('2023-10-26T15:00:00Z')
        t1_c3 = t1.comment_set.create(comment='c', created_at=t1_c3_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.context_data['ticket'], t1)
        self.assertQuerySetEqual(resp.context_data['comment_list'], [t1_c2, t1_c3, t1_c1])
        self.assertEqual(resp.status_code, 200)

    def test_options(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.options('/')
        req.user = AnonymousUser()
        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 200)

    def test_head(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.head('/')
        req.user = AnonymousUser()
        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 200)

    def test_post(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.post('/')
        req.user = AnonymousUser()
        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 405)

    def test_put(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.put('/')
        req.user = AnonymousUser()
        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 405)

    def test_patch(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.patch('/')
        req.user = AnonymousUser()
        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 405)

    def test_delete(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.delete('/')
        req.user = AnonymousUser()
        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 405)

    def test_trace(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.trace('/')
        req.user = AnonymousUser()
        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 405)


class CreateCommentViewTest(TestCase):
    '''
    コメントを期待通り作れるか確認する。各期待しないパラメータについて
    は、原則他のすべてのパラメータは期待の値にして検証する。
    '''

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_shimon = User.objects.create_user(
            'shimon', 'shimon@example.com', 'pw')

    def setUp(self):
        super().setUp()
        self.req_factory = RequestFactory()

    def test_anon(self):
        '''
        未ログインはコメント不可
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)

        req = self.req_factory.post('/', data={'key': t1.key, 'comment': 'c'})
        req.user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            CreateCommentView.as_view()(req)
        self.assertQuerySetEqual(t1.comment_set.all(), [])

    def test_ok(self):
        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)

        self.assertQuerySetEqual(t1.comment_set.all(), [])

        t1_c1_comment = 'c'
        req = self.req_factory.post('/', data={'key': t1.key, 'comment': t1_c1_comment})
        req.user = self.user_shimon

        resp = CreateCommentView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('page:ticket_detail_page', kwargs={'key': t1.key}))
        self.assertQuerySetEqual(t1.comment_set.all(), [t1.comment_set.get(comment=t1_c1_comment)])

    def test_extra_data(self):
        '''
        POSTで余計なデータが来た場合は余計なデータを無視して成功
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)

        self.assertQuerySetEqual(t1.comment_set.all(), [])

        t1_c1_comment = 'c'
        req = self.req_factory.post('/', data={'key': t1.key, 'comment': t1_c1_comment, 'extra': 'extra'})
        req.user = self.user_shimon

        resp = CreateCommentView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('page:ticket_detail_page', kwargs={'key': t1.key}))
        self.assertQuerySetEqual(t1.comment_set.all(), [t1.comment_set.get(comment=t1_c1_comment)])

    def test_empty_comment(self):
        '''
        コメントが空文字列の場合は成功
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)

        self.assertQuerySetEqual(t1.comment_set.all(), [])

        t1_c1_comment = ''
        req = self.req_factory.post('/', data={'key': t1.key, 'comment': t1_c1_comment})
        req.user = self.user_shimon

        resp = CreateCommentView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('page:ticket_detail_page', kwargs={'key': t1.key}))
        self.assertQuerySetEqual(t1.comment_set.all(), [t1.comment_set.get(comment=t1_c1_comment)])

    def test_invalid_ticket(self):
        '''
        存在しないチケットを指定した場合は例外を送出
        '''

        key = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d5d')
        self.assertQuerySetEqual(Ticket.objects.all(), [])
        self.assertQuerySetEqual(Comment.objects.all(), [])

        c1_comment = 'c'
        req = self.req_factory.post('/', data={'key': key, 'comment': c1_comment})
        req.user = self.user_shimon
        with self.assertRaises(ObjectDoesNotExist):
            CreateCommentView.as_view()(req)
        self.assertQuerySetEqual(Comment.objects.all(), [])

    def test_no_comment(self):
        '''
        コメントが無い場合は例外を送出
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)

        self.assertQuerySetEqual(t1.comment_set.all(), [])

        req = self.req_factory.post('/', data={'key': t1.key})
        req.user = self.user_shimon

        with self.assertRaises(Exception):
            CreateCommentView.as_view()(req)
        self.assertQuerySetEqual(t1.comment_set.all(), [])

    def test_too_long_comment(self):
        '''
        コメントが長すぎるときは成功
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)

        self.assertQuerySetEqual(t1.comment_set.all(), [])

        t1_c1_comment = 'c' * 1024 * 1024
        req = self.req_factory.post('/', data={'key': t1.key, 'comment': t1_c1_comment})
        req.user = self.user_shimon

        resp = CreateCommentView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('page:ticket_detail_page', kwargs={'key': t1.key}))
        self.assertQuerySetEqual(t1.comment_set.all(), [t1.comment_set.get(comment=t1_c1_comment)])

    def test_invalid_ticket_and_too_long_comment(self):
        '''
        存在しないチケットを指定し、コメントが長すぎる場合は例外を送出
        '''

        key = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d5d')
        self.assertQuerySetEqual(Ticket.objects.all(), [])
        self.assertQuerySetEqual(Comment.objects.all(), [])

        c1_comment = 'c' * 1024 * 1024
        req = self.req_factory.post('/', data={'key': key, 'comment': c1_comment})
        req.user = self.user_shimon
        with self.assertRaises(ObjectDoesNotExist):
            CreateCommentView.as_view()(req)
        self.assertQuerySetEqual(Comment.objects.all(), [])

    def test_options(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        t1_c1_comment = 'c'
        req = self.req_factory.options('/', data={'key': t1.key, 'comment': t1_c1_comment})
        req.user = self.user_shimon
        resp = CreateCommentView.as_view()(req)
        self.assertEqual(resp.status_code, 200)

    def test_head(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        t1_c1_comment = 'c'
        req = self.req_factory.head('/', data={'key': t1.key, 'comment': t1_c1_comment})
        req.user = self.user_shimon
        resp = CreateCommentView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_get(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        t1_c1_comment = 'c'
        req = self.req_factory.get('/', data={'key': t1.key, 'comment': t1_c1_comment})
        req.user = self.user_shimon
        resp = CreateCommentView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_put(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        t1_c1_comment = 'c'
        req = self.req_factory.put('/', data={'key': t1.key, 'comment': t1_c1_comment})
        req.user = self.user_shimon
        resp = CreateCommentView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_patch(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        t1_c1_comment = 'c'
        req = self.req_factory.patch('/', data={'key': t1.key, 'comment': t1_c1_comment})
        req.user = self.user_shimon
        resp = CreateCommentView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_delete(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        t1_c1_comment = 'c'
        req = self.req_factory.delete('/', data={'key': t1.key, 'comment': t1_c1_comment})
        req.user = self.user_shimon
        resp = CreateCommentView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_trace(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        t1_c1_comment = 'c'
        req = self.req_factory.trace('/', data={'key': t1.key, 'comment': t1_c1_comment})
        req.user = self.user_shimon
        resp = CreateCommentView.as_view()(req)
        self.assertEqual(resp.status_code, 405)


class FilePageViewTest(TestCase):
    '''
    ファイルが期待通りの順序で一覧表示されることを確認する。
    '''

    def setUp(self):
        super().setUp()
        self.req_factory = RequestFactory()

    def test_empty(self):
        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['file_list'], [])
        self.assertEqual(resp.context_data['constant_map'],
                         {'url_map': {name: reverse(name) for name in ['page:file:upload']}})
        self.assertEqual(resp.status_code, 200)

    def test_one(self):
        un = 'shimon'
        f1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        f1 = UploadedFile.objects.create(name='f', last_modified=f1_dt, size='0', username=un)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['file_list'], [f1])
        self.assertEqual(resp.context_data['constant_map'],
                         {'url_map': {name: reverse(name) for name in ['page:file:upload']}})
        self.assertEqual(resp.status_code, 200)

    def test_two(self):
        '''
        ファイルは、ファイル名、最終変更日時、キーの順番で昇順にソート
        される。
        '''

        un = 'shimon'
        f1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        f1 = UploadedFile.objects.create(name='g', last_modified=f1_dt, size='0', username=un)
        f2_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        f2 = UploadedFile.objects.create(name='f', last_modified=f2_dt, size='0', username=un)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['file_list'], [f2, f1])
        self.assertEqual(resp.context_data['constant_map'],
                         {'url_map': {name: reverse(name) for name in ['page:file:upload']}})
        self.assertEqual(resp.status_code, 200)

    def test_three(self):
        '''
        ファイルは、ファイル名、最終変更日時、キーの順番で昇順にソート
        される。
        '''

        un = 'shimon'
        f1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        f1 = UploadedFile.objects.create(name='g', last_modified=f1_dt, size='0', username=un)
        f2_dt = datetime.datetime.fromisoformat('2023-10-10T23:50:00Z')
        f2 = UploadedFile.objects.create(name='f', last_modified=f2_dt, size='0', username=un)
        f3_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        f3 = UploadedFile.objects.create(name='f', last_modified=f3_dt, size='0', username=un)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['file_list'], [f2, f3, f1])
        self.assertEqual(resp.context_data['constant_map'],
                         {'url_map': {name: reverse(name) for name in ['page:file:upload']}})
        self.assertEqual(resp.status_code, 200)

    def test_eight(self):
        '''
        ファイルは、ファイル名、最終変更日時、キーの順番で昇順にソート
        される。
        '''

        un = 'shimon'
        f1_dt = datetime.datetime.fromisoformat('2023-10-15T23:50:00Z')
        f1_k = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d5d')
        f1 = UploadedFile.objects.create(key=f1_k, name='g', last_modified=f1_dt, size='0', username=un)
        f2_k = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d53')
        f2_dt = datetime.datetime.fromisoformat('2023-10-15T23:50:00Z')
        f2 = UploadedFile.objects.create(key=f2_k, name='g', last_modified=f2_dt, size='1', username=un)
        f3_k = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d5f')
        f3_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        f3 = UploadedFile.objects.create(key=f3_k, name='f', last_modified=f3_dt, size='2', username=un)
        f4_k = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d59')
        f4_dt = datetime.datetime.fromisoformat('2023-10-08T23:20:00Z')
        f4 = UploadedFile.objects.create(key=f4_k, name='g', last_modified=f4_dt, size='3', username=un)
        f5_k = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d51')
        f5_dt = datetime.datetime.fromisoformat('2023-10-10T23:50:00Z')
        f5 = UploadedFile.objects.create(key=f5_k, name='f', last_modified=f5_dt, size='4', username=un)
        f6_k = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d55')
        f6_dt = datetime.datetime.fromisoformat('2023-10-08T23:20:00Z')
        f6 = UploadedFile.objects.create(key=f6_k, name='g', last_modified=f6_dt, size='5', username=un)
        f7_k = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d52')
        f7_dt = datetime.datetime.fromisoformat('2023-10-10T23:50:00Z')
        f7 = UploadedFile.objects.create(key=f7_k, name='f', last_modified=f7_dt, size='6', username=un)
        f8_k = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d5a')
        f8_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        f8 = UploadedFile.objects.create(key=f8_k, name='f', last_modified=f8_dt, size='7', username=un)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['file_list'],
                                 [f5, f7, f8, f3, f6, f4, f2, f1])
        self.assertEqual(resp.context_data['constant_map'],
                         {'url_map': {name: reverse(name) for name in ['page:file:upload']}})
        self.assertEqual(resp.status_code, 200)

    def test_options(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.options('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertEqual(resp.status_code, 200)

    def test_head(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.head('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertEqual(resp.status_code, 200)

    def test_post(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.post('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_put(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.put('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_patch(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.patch('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_delete(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.delete('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_trace(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.trace('/')
        req.user = AnonymousUser()
        resp = FilePageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)


class CreateFileViewTest(TestCase):
    '''
    ファイルを期待通り作れるか確認する。各期待しないパラメータについて
    は、他のすべてのパラメータは期待の値にして検証する。
    '''

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_shimon = User.objects.create_user(
            'shimon', 'shimon@example.com', 'pw')
        # 実際にアップロードしようとすると、タイミングの問題でS3にアク
        # セスできない。S3にアクセスする必要はないので、テストでは
        # upload_blobを使わず、単にオブジェクトを作成しておく。
        cls.s3uploader = S3Uploader.objects.create(
            status=S3Uploader.COMPLETED, username=cls.user_shimon.username, size=6)

    def setUp(self):
        super().setUp()
        self.req_factory = RequestFactory()

    def test_anon(self):
        '''
        未ログインはファイル作成不可
        '''

        req = self.req_factory.post('/', data={'blobkey': self.s3uploader.key, 'filename': 'hello.txt'})
        req.user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            CreateFileView.as_view()(req)
        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.s3uploader])

    def test_ok(self):
        f1_name = 'hello.txt'
        req = self.req_factory.post('/', data={'blobkey': self.s3uploader.key, 'filename': f1_name})
        req.user = self.user_shimon

        resp = CreateFileView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('page:file_page'))
        self.assertQuerySetEqual(UploadedFile.objects.all(), [UploadedFile.objects.get(name=f1_name)])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [])

    def test_extra_data(self):
        '''
        POSTで余計なデータが来た場合は余計なデータを無視して成功
        '''

        f1_name = 'hello.txt'
        req = self.req_factory.post('/', data={'blobkey': self.s3uploader.key, 'filename': f1_name, 'extra': 'extra'})
        req.user = self.user_shimon

        resp = CreateFileView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('page:file_page'))
        self.assertQuerySetEqual(UploadedFile.objects.all(), [UploadedFile.objects.get(name=f1_name)])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [])

    def test_invalid_blobkey(self):
        '''
        指定したブロブが無ければ例外を送出
        '''

        key = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d5d')
        req = self.req_factory.post('/', data={'blobkey': key, 'filename': 'hello.txt'})
        req.user = self.user_shimon

        with self.assertRaises(ObjectDoesNotExist):
            CreateFileView.as_view()(req)
        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.s3uploader])

    def test_empty_blobkey(self):
        '''
        ブロブキーが空文字列なら例外を送出
        '''

        req = self.req_factory.post('/', data={'blobkey': '', 'filename': 'hello.txt'})
        req.user = self.user_shimon

        with self.assertRaises(ValidationError):
            CreateFileView.as_view()(req)
        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.s3uploader])

    def test_no_blobkey(self):
        '''
        ブロブキーが無いなら例外を送出
        '''

        req = self.req_factory.post('/', data={'filename': 'hello.txt'})
        req.user = self.user_shimon

        with self.assertRaises(Exception):
            CreateFileView.as_view()(req)
        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.s3uploader])

    def test_no_filename(self):
        '''
        ファイル名が無いなら例外を送出
        '''

        req = self.req_factory.post('/', data={'blobkey': self.s3uploader.key})
        req.user = self.user_shimon

        with self.assertRaises(Exception):
            CreateFileView.as_view()(req)
        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.s3uploader])

    def test_empty_filename(self):
        f1_name = ''
        req = self.req_factory.post('/', data={'blobkey': self.s3uploader.key, 'filename': f1_name})
        req.user = self.user_shimon

        resp = CreateFileView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('page:file_page'))
        self.assertQuerySetEqual(UploadedFile.objects.all(), [UploadedFile.objects.get(name=f1_name)])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [])

    def test_too_long_filename(self):
        '''
        ファイル名が長すぎるなら例外を送出
        '''

        f1_name = ''.join(random.Random(0).choices(string.ascii_lowercase, k=256))
        req = self.req_factory.post('/', data={'blobkey': self.s3uploader.key, 'filename': f1_name})
        req.user = self.user_shimon

        with self.assertRaises(DataError):
            CreateFileView.as_view()(req)
        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.s3uploader])

    def test_invalid(self):
        '''
        いずれのパラメーターも無効なら例外を送出
        '''

        key = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d5d')
        f1_name = ''.join(random.Random(0).choices(string.ascii_lowercase, k=256))
        req = self.req_factory.post('/', data={'blobkey': key, 'filename': f1_name})
        req.user = self.user_shimon

        with self.assertRaises(Exception):
            CreateFileView.as_view()(req)
        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.s3uploader])

    def test_no(self):
        '''
        いずれのパラメーターも無いなら例外を送出
        '''

        req = self.req_factory.post('/', data={})
        req.user = self.user_shimon

        with self.assertRaises(Exception):
            CreateFileView.as_view()(req)
        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.s3uploader])

    def test_other_user_blob(self):
        '''
        他ユーザーのブロブを横取りしてファイルを作ることは出来ない。
        '''

        self.s3uploader.username = 'john'
        self.s3uploader.save()

        f1_name = 'hello.txt'
        req = self.req_factory.post('/', data={'blobkey': self.s3uploader.key, 'filename': f1_name})
        req.user = self.user_shimon

        with self.assertRaises(ObjectDoesNotExist):
            CreateFileView.as_view()(req)
        self.assertQuerySetEqual(UploadedFile.objects.all(), [])
        self.assertQuerySetEqual(S3Uploader.objects.all(), [self.s3uploader])

    def test_options(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.options('/')
        req.user = self.user_shimon
        resp = CreateFileView.as_view()(req)
        self.assertEqual(resp.status_code, 200)

    def test_head(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.head('/')
        req.user = self.user_shimon
        resp = CreateFileView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_get(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.get('/')
        req.user = self.user_shimon
        resp = CreateFileView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_put(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.put('/')
        req.user = self.user_shimon
        resp = CreateFileView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_patch(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.patch('/')
        req.user = self.user_shimon
        resp = CreateFileView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_delete(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.delete('/')
        req.user = self.user_shimon
        resp = CreateFileView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_trace(self):
        '''
        基本的なアクションはPOSTに限る
        '''

        req = self.req_factory.trace('/')
        req.user = self.user_shimon
        resp = CreateFileView.as_view()(req)
        self.assertEqual(resp.status_code, 405)


class TopPageViewTest(TestCase):
    def setUp(self):
        super().setUp()
        self.req_factory = RequestFactory()

    def test_ok(self):
        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TopPageView.as_view()(req)
        self.assertEqual(resp.context_data['text'], settings.TOPPAGE_TEXT)
        self.assertEqual(resp.status_code, 200)

    def test_options(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.options('/')
        req.user = AnonymousUser()
        resp = TopPageView.as_view()(req)
        self.assertEqual(resp.status_code, 200)

    def test_head(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.head('/')
        req.user = AnonymousUser()
        resp = TopPageView.as_view()(req)
        self.assertEqual(resp.status_code, 200)

    def test_post(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.post('/')
        req.user = AnonymousUser()
        resp = TopPageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_put(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.put('/')
        req.user = AnonymousUser()
        resp = TopPageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_patch(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.patch('/')
        req.user = AnonymousUser()
        resp = TopPageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_delete(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.delete('/')
        req.user = AnonymousUser()
        resp = TopPageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_trace(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.trace('/')
        req.user = AnonymousUser()
        resp = TopPageView.as_view()(req)
        self.assertEqual(resp.status_code, 405)
