# messaging-api

Provides API end point to be called to send emails. Useful in cloud services like Oracle Cloud free tier ATP where Oracle has blocked the SMTP. This API or a version of it can be used by the APEX / ORDS / Oracle database to send emails.

While most of the API is quite generic in nature and can be used by anyone, it is still not a very generic service in the sense that the **_app_data_** is very specific to my use case and hence the template. But they are very easy to change. I will try to generalize at some point in time.

## Sample curl call

The access token can be passed in the HEADER, as a QUERY_PARAMETER or as a COOKIE. Its best to pass it as a HEADER and not in QUERY PARAMETER.

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/send_email' \
  -H 'accept: application/json' \
  -H 'access_token: 1234567asdfgh' \
  -H 'Content-Type: application/json' \
  -d '{
  "mail_connection_parameters": {"host": "mail.google.com", "port": "587", "login": "someemail@gmail.com", "password": "password. in case of gmail create application password"},
  "mail_headers": {"From": "someemail@gmail.com", "To": "customer@domain.com", "Subject": "Your Order Number [1099] Received", "Reply-To": "no-reply@katrankalakari.itas.in"},
  "app_data": {"customer_name": "Customer_Name", "order_number": "1099", "email_template": "katran_kalakari.txt"}
}'
```
