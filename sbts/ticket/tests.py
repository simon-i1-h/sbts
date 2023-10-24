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

        dt = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket', created_at=dt)

        tickets = Ticket.objects.sorted_tickets()
        self.assertQuerySetEqual(tickets, [t1])

    def test_2(self):
        '''
        チケットは常に降順で返される
        '''
        dt1 = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)
        dt2 = datetime.datetime.fromisoformat('2023-10-24T23:00:00Z')
        t2 = Ticket.objects.create(title='ticket 2', created_at=dt2)

        tickets = Ticket.objects.sorted_tickets()
        self.assertQuerySetEqual(tickets, [t2, t1])

    def test_3(self):
        '''
        チケットは常に降順で返される
        '''

        dt1 = datetime.datetime.fromisoformat('2023-10-23T23:20:00Z')
        t1 = Ticket.objects.create(title='ticket 1', created_at=dt1)
        dt2 = datetime.datetime.fromisoformat('2023-10-24T23:00:00Z')
        t2 = Ticket.objects.create(title='ticket 2', created_at=dt2)
        dt3 = datetime.datetime.fromisoformat('2023-10-22T23:50:00Z')
        t3 = Ticket.objects.create(title='ticket 3', created_at=dt3)

        tickets = Ticket.objects.sorted_tickets()
        self.assertQuerySetEqual(tickets, [t2, t1, t3])
