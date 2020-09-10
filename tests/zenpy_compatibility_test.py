import os

from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket, User, Comment
from zenpy.lib.exception import APIException

USERNAME = os.environ["MOCK_ZENDESK_USERNAME"]
API_KEY = os.environ["MOCK_ZENDESK_API_KEY"]


def _main():
    zendesk_client = Zenpy(
        subdomain="legalstart",
        token=API_KEY,
        email=USERNAME,
        disable_cache=True,
    )
    x = zendesk_client.search(type="ticket", external_id="42")

    new_ticket = zendesk_client.tickets.create(
        Ticket(
           description='Some description',
            comment=Comment(body="first comment"),
           requester=User(name='bob', email='bob@example.com'),
            tags=["1" , "2"],
            external_id="42")
    )


    ticket = zendesk_client.tickets(id=new_ticket.id)
    ticket.comment = Comment(body="Important private comment", public=False)
    ticket.tags.extend(["3, 4"])
    zendesk_client.tickets.update(ticket)

    for comment in zendesk_client.tickets.comments(ticket=ticket.id):
        print(comment.body)

    updated_ticket = zendesk_client.tickets(id=new_ticket.id)
    print(ticket.tags)

    zendesk_client.tickets.delete(new_ticket)
    try:
        deletedTicket = zendesk_client.tickets(id=new_ticket.id)
    except APIException as e:
        if e.response.status_code == 404:
            print("Ticket deleted successfully")

_main()
