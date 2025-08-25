-- disable culqi payment provider
UPDATE payment_provider
   SET culqi_public_key = NULL,
       culqi_private_key = NULL;
