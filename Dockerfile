FROM python:3.8-alpine
COPY mock_zendesk/ mock_zendesk/
ENV  MOCK_ZENDESK_PORT 80
EXPOSE 80
CMD ["python", "-u", "-m" , "mock_zendesk"]
