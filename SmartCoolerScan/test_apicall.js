'use strict';

const fs = require('fs');

const Client = require('./client.js');

const configArgs = {
    'publicKeyId' : 'AG23AX7S6ITTRB7UWFNIDM26',
    'privateKey' : fs.readFileSync('my_private_key.txt'),
    'region' : 'jp',
    'sandbox' : true
};

function createCheckoutSession(payload, headers) {
    console.log('-------------[CREATE CHECKOUT SESSION]-------------');
    client.apiCall({
        method: 'POST',
        urlFragment: 'v1/checkoutSessions',
        payload: payload,
        headers: headers
    }).then(function (result) {
        console.log('SUCCESS: statusCode=' + result.statusCode);
        const responseObject = JSON.parse(result.body);
        console.dir(responseObject, { depth: null });
        getCheckoutSession(responseObject.checkoutSessionId);
    }).catch(err => {
        console.error('ERROR: statusCode=' + err.statusCode);
        console.dir(JSON.parse(err.body), { depth: null });
    });
}

function getCheckoutSession(checkoutSessionId) {
    console.log('\n\n-------------[GET CHECKOUT SESSION]-------------');
    client.apiCall({
        method: 'GET',
        urlFragment: 'v1/checkoutSessions/' + checkoutSessionId
    }).then(function (result) {
        console.log('SUCCESS: statusCode=' + result.statusCode);
        console.dir(JSON.parse(result.body), { depth: null });
    }).catch(err => {
        console.error('ERROR: statusCode=' + err.statusCode);
        console.dir(JSON.parse(err.body), { depth: null });
    });
}

const client = new Client(configArgs);

//const payload = '{ "webCheckoutDetail": { "checkoutReviewReturnUrl" : "https://localhost/maxo/preconfirm.php" }, "storeId" : "amzn1.application-oa2-client.d9da4374abb24732a174be549d99eb7a" }';
const payload = {
    webCheckoutDetail: {
        checkoutReviewReturnUrl: 'https://localhost/maxo/preconfirm.php'
    },
    storeId: 'amzn1.application-oa2-client.eef53cd200af4140be574e1a44e9576c'
};

createCheckoutSession(payload, { 'x-amz-pay-idempotency-key': '942f70df7b7b46aa9a8da10a3aa4aba0' } );
// createCheckoutSession(payload, { 'x-amz-pay-idempotency-key': uuidv4().toString().replace(/-/g, '') } );

