'use strict';

const fs = require('fs');

const Client = require('./client.js');

const configArgs = {
    'publicKeyId' : 'AG23AX7S6ITTRB7UWFNIDM26',
    'privateKey' : fs.readFileSync('my_private_key.txt'),
    'region' : 'jp',
    'sandbox' : true
};

const client = new Client(configArgs);

//const payload = '{ "webCheckoutDetails": { "checkoutReviewReturnUrl" : "https://localhost/maxo/preconfirm.php" }, "storeId" : "amzn1.application-oa2-client.d9da4374abb24732a174be549d99eb7a" }';
const payload = {
    webCheckoutDetails: {
        checkoutReviewReturnUrl: 'https://localhost/maxo/preconfirm.php'
    },
    storeId: 'amzn1.application-oa2-client.eef53cd200af4140be574e1a44e9576c'
};

console.log('-------------[CREATE CHECKOUT SESSION HEADERS]-------------');
let signedHeaders = client.getSignedHeaders({
    method: 'POST',
    urlFragment: 'v1/checkoutSessions',
    payload: payload,
    headers: { 'x-amz-pay-idempotency-key': '942f70df7b7b46aa9a8da10a3aa4aba0' }
});
console.log(signedHeaders);

console.log('\n\n-------------[GET CHECKOUT SESSION HEADERS]-------------');
signedHeaders = client.getSignedHeaders({
    method: 'GET',
    urlFragment: 'v1/checkoutSessions/7c5005d5-0697-4c9c-8ec5-08f487206368'
});
console.log(signedHeaders);
