import datetime
import uuid

from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .templatetags.pretty_filters import pretty_nbytes
from .views import TicketPageView, CreateTicketView, TicketDetailPageView
from sbts.ticket.models import Ticket


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
        self.req_factory = RequestFactory()

    def test_empty(self):
        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [])
        self.assertEqual(resp.status_code, 200)

    def test_one(self):
        dt1 = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='a', created_at=dt1)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t1])
        self.assertEqual(resp.status_code, 200)

    def test_two(self):
        '''
        チケットの一覧はチケットの作成日時の降順になる。
        '''

        dt1 = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='b', created_at=dt1)
        dt2 = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='a', created_at=dt2)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t2, t1])
        self.assertEqual(resp.status_code, 200)

    def test_three(self):
        '''
        チケットの一覧はチケットの作成日時の降順になる。
        '''

        dt1 = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='c', created_at=dt1)
        dt2 = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='b', created_at=dt2)
        dt3 = datetime.datetime.fromisoformat('2023-10-24T03:15:00Z')
        t3 = Ticket.objects.create(title='a', created_at=dt3)

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

        dt1 = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='c', created_at=dt1)
        c1 = datetime.datetime.fromisoformat('2023-10-23T23:20:15Z')
        t1.comment_set.create(comment='a', created_at=c1)

        dt2 = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='b', created_at=dt2)
        # 何故かチケット作成日よりコメント日の方が早いが、許容する
        c2 = datetime.datetime.fromisoformat('2023-10-22T11:00:30Z')
        t2.comment_set.create(comment='b', created_at=c2)

        dt3 = datetime.datetime.fromisoformat('2023-10-24T03:15:00Z')
        t3 = Ticket.objects.create(title='a', created_at=dt3)
        c3 = datetime.datetime.fromisoformat('2023-10-24T23:00:30Z')
        t3.comment_set.create(comment='c', created_at=c3)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t2, t3, t1])
        self.assertEqual(resp.context_data['ticket_list'][0].lastmod, c2)
        self.assertEqual(resp.context_data['ticket_list'][1].lastmod, c3)
        self.assertEqual(resp.context_data['ticket_list'][2].lastmod, c1)
        self.assertEqual(resp.status_code, 200)

    def test_comment_two(self):
        '''
        チケットにコメントがあっても、チケットの一覧はチケットの作成日
        時の降順になる。

        最終変更日は、コメントがあれば最新コメント日時に、なければチケッ
        トの作成日になる。
        '''

        dt1 = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='c', created_at=dt1)
        c1_1 = datetime.datetime.fromisoformat('2023-10-23T23:20:30Z')
        t1.comment_set.create(comment='a', created_at=c1_1)
        c1_2 = datetime.datetime.fromisoformat('2023-10-23T23:20:15Z')
        t1.comment_set.create(comment='b', created_at=c1_2)

        dt2 = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='b', created_at=dt2)
        # 何故かチケット作成日よりコメント日の方が早いが、許容する
        c2_1 = datetime.datetime.fromisoformat('2023-10-22T11:00:15Z')
        t2.comment_set.create(comment='c', created_at=c2_1)
        c2_2 = datetime.datetime.fromisoformat('2023-10-22T11:00:30Z')
        t2.comment_set.create(comment='d', created_at=c2_2)

        dt3 = datetime.datetime.fromisoformat('2023-10-24T03:15:00Z')
        t3 = Ticket.objects.create(title='a', created_at=dt3)
        c3_1 = datetime.datetime.fromisoformat('2023-10-24T23:05:00Z')
        t3.comment_set.create(comment='e', created_at=c3_1)
        c3_2 = datetime.datetime.fromisoformat('2023-10-24T23:00:00Z')
        t3.comment_set.create(comment='f', created_at=c3_2)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t2, t3, t1])
        self.assertEqual(resp.context_data['ticket_list'][0].lastmod, c2_2)
        self.assertEqual(resp.context_data['ticket_list'][1].lastmod, c3_1)
        self.assertEqual(resp.context_data['ticket_list'][2].lastmod, c1_1)
        self.assertEqual(resp.status_code, 200)

    def test_comment_three(self):
        '''
        チケットにコメントがあっても、チケットの一覧はチケットの作成日
        時の降順になる。

        最終変更日は、コメントがあれば最新コメント日時に、なければチケッ
        トの作成日になる。
        '''

        dt1 = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='c', created_at=dt1)
        c1_1 = datetime.datetime.fromisoformat('2023-10-23T23:20:30Z')
        t1.comment_set.create(comment='a', created_at=c1_1)
        c1_2 = datetime.datetime.fromisoformat('2023-10-23T23:20:15Z')
        t1.comment_set.create(comment='b', created_at=c1_2)
        c1_3 = datetime.datetime.fromisoformat('2023-10-23T23:20:40Z')
        t1.comment_set.create(comment='c', created_at=c1_3)

        dt2 = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='b', created_at=dt2)
        # 何故かチケット作成日よりコメント日の方が早いが、許容する
        c2_1 = datetime.datetime.fromisoformat('2023-10-22T11:01:00Z')
        t2.comment_set.create(comment='d', created_at=c2_1)
        c2_2 = datetime.datetime.fromisoformat('2023-10-22T11:00:30Z')
        t2.comment_set.create(comment='e', created_at=c2_2)
        c2_3 = datetime.datetime.fromisoformat('2023-10-22T11:00:00Z')
        t2.comment_set.create(comment='f', created_at=c2_3)

        dt3 = datetime.datetime.fromisoformat('2023-10-24T03:15:00Z')
        t3 = Ticket.objects.create(title='a', created_at=dt3)
        c3_1 = datetime.datetime.fromisoformat('2023-10-24T23:00:00Z')
        t3.comment_set.create(comment='g', created_at=c3_1)
        c3_2 = datetime.datetime.fromisoformat('2023-10-25T01:00:00Z')
        t3.comment_set.create(comment='h', created_at=c3_2)
        c3_3 = datetime.datetime.fromisoformat('2023-10-24T23:00:10Z')
        t3.comment_set.create(comment='i', created_at=c3_3)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t2, t3, t1])
        self.assertEqual(resp.context_data['ticket_list'][0].lastmod, c2_1)
        self.assertEqual(resp.context_data['ticket_list'][1].lastmod, c3_2)
        self.assertEqual(resp.context_data['ticket_list'][2].lastmod, c1_3)
        self.assertEqual(resp.status_code, 200)

    def test_ticket_and_comment(self):
        '''
        チケットにコメントがあっても、チケットの一覧はチケットの作成日
        時の降順になる。

        最終変更日は、コメントがあれば最新コメント日時に、なければチケッ
        トの作成日になる。
        '''

        dt1 = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='c', created_at=dt1)
        c1 = datetime.datetime.fromisoformat('2023-10-23T23:20:15Z')
        t1.comment_set.create(comment='a', created_at=c1)

        dt2 = datetime.datetime.fromisoformat('2023-10-24T11:00:00Z')
        t2 = Ticket.objects.create(title='b', created_at=dt2)

        dt3 = datetime.datetime.fromisoformat('2023-10-24T03:15:00Z')
        t3 = Ticket.objects.create(title='a', created_at=dt3)
        c3_1 = datetime.datetime.fromisoformat('2023-10-24T23:00:30Z')
        t3.comment_set.create(comment='d', created_at=c3_1)
        c3_2 = datetime.datetime.fromisoformat('2023-10-25T05:00:30Z')
        t3.comment_set.create(comment='c', created_at=c3_2)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketPageView.as_view()(req)
        self.assertQuerySetEqual(resp.context_data['ticket_list'], [t2, t3, t1])
        self.assertEqual(resp.context_data['ticket_list'][0].lastmod, dt2)
        self.assertEqual(resp.context_data['ticket_list'][1].lastmod, c3_2)
        self.assertEqual(resp.context_data['ticket_list'][2].lastmod, c1)
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
        cls.user_shimon = User.objects.create_user(
            'shimon', 'shimon@example.com', 'pw')

    def setUp(self):
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
        self.assertEqual(resp['Location'], reverse('ticket'))
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
        self.assertEqual(resp['Location'], reverse('ticket'))
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
        self.assertEqual(resp['Location'], reverse('ticket'))
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
        self.assertEqual(resp['Location'], reverse('ticket'))
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
        self.req_factory = RequestFactory()

    def test_invalid_ticket(self):
        '''
        指定したチケットが存在しなければ例外を送出
        '''

        id = uuid.UUID('6b1ec55f-3e41-4780-aa71-0fbbbe4e0d5d')
        self.assertQuerySetEqual(Ticket.objects.all(), [])

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        with self.assertRaises(ObjectDoesNotExist):
            TicketDetailPageView.as_view()(req, key=id)

    def test_empty(self):
        dt1 = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertQuerySetEqual(resp.context_data['comment_list'], [])
        self.assertEqual(resp.status_code, 200)

    def test_one(self):
        dt1 = datetime.datetime.fromisoformat('2023-10-22T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)

        c1_dt = datetime.datetime.fromisoformat('2023-10-26T15:00:00Z')
        c1 = t1.comment_set.create(comment='a', created_at=c1_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.context_data['ticket'], t1)
        self.assertQuerySetEqual(resp.context_data['comment_list'], [c1])
        self.assertEqual(resp.status_code, 200)

    def test_two(self):
        '''
        コメントの一覧はコメントの作成日時の昇順になる。
        '''
        dt1 = datetime.datetime.fromisoformat('2023-10-22T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)

        c1_dt = datetime.datetime.fromisoformat('2023-10-26T20:00:00Z')
        c1 = t1.comment_set.create(comment='a', created_at=c1_dt)
        c2_dt = datetime.datetime.fromisoformat('2023-10-26T15:00:00Z')
        c2 = t1.comment_set.create(comment='b', created_at=c2_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.context_data['ticket'], t1)
        self.assertQuerySetEqual(resp.context_data['comment_list'], [c2, c1])
        self.assertEqual(resp.status_code, 200)

    def test_three(self):
        '''
        コメントの一覧はコメントの作成日時の昇順になる。
        '''
        dt1 = datetime.datetime.fromisoformat('2023-10-22T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)

        c1_dt = datetime.datetime.fromisoformat('2023-10-26T20:00:00Z')
        c1 = t1.comment_set.create(comment='a', created_at=c1_dt)
        c2_dt = datetime.datetime.fromisoformat('2023-10-26T09:00:00Z')
        c2 = t1.comment_set.create(comment='b', created_at=c2_dt)
        c3_dt = datetime.datetime.fromisoformat('2023-10-26T15:00:00Z')
        c3 = t1.comment_set.create(comment='c', created_at=c3_dt)

        req = self.req_factory.get('/')
        req.user = AnonymousUser()
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.context_data['ticket'], t1)
        self.assertQuerySetEqual(resp.context_data['comment_list'], [c2, c3, c1])
        self.assertEqual(resp.status_code, 200)

    def test_options(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.options('/')
        req.user = AnonymousUser()
        dt1 = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 200)

    def test_head(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.head('/')
        req.user = AnonymousUser()
        dt1 = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 200)

    def test_post(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.post('/')
        req.user = AnonymousUser()
        dt1 = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 405)

    def test_put(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.put('/')
        req.user = AnonymousUser()
        dt1 = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 405)

    def test_patch(self):
        '''
        基本的なアクションはGETに限る
        '''

        req = self.req_factory.patch('/')
        req.user = AnonymousUser()
        dt1 = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 405)

    def test_delete(self):
        '''
        基本的なアクションはGETに限る
        '''
        req = self.req_factory.delete('/')
        req.user = AnonymousUser()
        dt1 = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 405)

    def test_trace(self):
        '''
        基本的なアクションはGETに限る
        '''
        req = self.req_factory.trace('/')
        req.user = AnonymousUser()
        dt1 = datetime.datetime.fromisoformat('2023-10-26T00:00:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)
        resp = TicketDetailPageView.as_view()(req, key=t1.key)
        self.assertEqual(resp.status_code, 405)
