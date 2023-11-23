import datetime

from django.test import TestCase

from .models import Ticket


class TicketSortedTicketsTest(TestCase):
    def test_0(self):
        '''
        チケットがないなら、当然空集合を返す
        '''

        self.assertQuerySetEqual(Ticket.objects.sorted_tickets(), [])

    def test_1(self):
        '''
        チケットが1つなら、単にそれだけを返す
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket', created_at=t1_dt)

        tickets = Ticket.objects.sorted_tickets()
        self.assertQuerySetEqual(tickets, [t1])

    def test_2(self):
        '''
        チケットは常に降順で返される
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        t2_dt = datetime.datetime.fromisoformat('2023-10-24T23:00:00Z')
        t2 = Ticket.objects.create(title='ticket 2', created_at=t2_dt)

        tickets = Ticket.objects.sorted_tickets()
        self.assertQuerySetEqual(tickets, [t2, t1])

    def test_3(self):
        '''
        チケットは常に降順で返される
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=t1_dt)
        t2_dt = datetime.datetime.fromisoformat('2023-10-24T23:00:00Z')
        t2 = Ticket.objects.create(title='ticket 2', created_at=t2_dt)
        t3_dt = datetime.datetime.fromisoformat('2023-10-22T23:50:00Z')
        t3 = Ticket.objects.create(title='ticket 3', created_at=t3_dt)

        tickets = Ticket.objects.sorted_tickets()
        self.assertQuerySetEqual(tickets, [t2, t1, t3])


class TicketSortedCommentsTest(TestCase):
    def test_0(self):
        '''
        コメントがないなら、当然空集合を返す
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket', created_at=t1_dt)

        self.assertQuerySetEqual(t1.sorted_comments(), [])

    def test_1(self):
        '''
        コメントが1つなら、単にそれだけを返す
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket', created_at=t1_dt)

        c1_dt = datetime.datetime.fromisoformat('2023-10-24T09:00:00Z')
        c1 = t1.comment_set.create(comment='a', created_at=c1_dt)

        self.assertQuerySetEqual(t1.sorted_comments(), [c1])

    def test_2(self):
        '''
        コメントは常に昇順で返される
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket', created_at=t1_dt)

        c1_dt = datetime.datetime.fromisoformat('2023-10-24T09:00:00Z')
        c1 = t1.comment_set.create(comment='a', created_at=c1_dt)
        c2_dt = datetime.datetime.fromisoformat('2023-10-24T08:00:00Z')
        c2 = t1.comment_set.create(comment='b', created_at=c2_dt)

        self.assertQuerySetEqual(t1.sorted_comments(), [c2, c1])

    def test_3(self):
        '''
        コメントは常に昇順で返される
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket', created_at=t1_dt)

        c1_dt = datetime.datetime.fromisoformat('2023-10-24T09:00:00Z')
        c1 = t1.comment_set.create(comment='a', created_at=c1_dt)
        c2_dt = datetime.datetime.fromisoformat('2023-10-24T08:00:00Z')
        c2 = t1.comment_set.create(comment='b', created_at=c2_dt)
        c3_dt = datetime.datetime.fromisoformat('2023-10-24T08:30:00Z')
        c3 = t1.comment_set.create(comment='c', created_at=c3_dt)

        self.assertQuerySetEqual(t1.sorted_comments(), [c2, c3, c1])


class TicketLastmodTest(TestCase):
    def test_no_comment(self):
        '''
        コメントがないなら、チケットの作成日を返す
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket', created_at=t1_dt)

        self.assertEqual(t1.lastmod, t1_dt)

    def test_comment_1(self):
        '''
        コメントがあるなら、一番新しいコメントの作成日を返す
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket', created_at=t1_dt)
        c1_dt = datetime.datetime.fromisoformat('2023-10-24T09:00:00Z')
        t1.comment_set.create(comment='a', created_at=c1_dt)

        self.assertEqual(t1.lastmod, c1_dt)

    def test_comment_2(self):
        '''
        コメントがあるなら、一番新しいコメントの作成日を返す
        '''

        t1_dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket', created_at=t1_dt)
        c1_dt = datetime.datetime.fromisoformat('2023-10-28T09:00:00Z')
        t1.comment_set.create(comment='a', created_at=c1_dt)
        c2_dt = datetime.datetime.fromisoformat('2023-10-24T10:00:00Z')
        t1.comment_set.create(comment='b', created_at=c2_dt)

        self.assertEqual(t1.lastmod, c1_dt)
