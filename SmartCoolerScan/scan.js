// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

exports.handler = (event, context, callback) => {

'use strict';

const fs = require('fs');

const Client = require('./client.js');

require('date-utils');
var dt = new Date();
var date = dt.toFormat("YYYYMMDDHH24MISS");
// console.log(date);


const configArgs = {
    'publicKeyId' : 'AG23AX7S6ITTRB7UWFNIDM26',
    'privateKey' : fs.readFileSync('./my_private_key.txt'),
    'region' : 'jp',
    'sandbox' : true
};

function merchantScan(payload, headers) {
    console.log('-------------[merchantScan]-------------');
    client.apiCall({
        method: 'POST',
        urlFragment: 'in-store/v1/merchantScan',
        payload: payload,
        headers: headers
    }).then(function (result) {
        console.log('SUCCESS: statusCode=' + result.statusCode);
        const responseObject = JSON.parse(result.body);
        console.dir(responseObject, { depth: null });
    }).catch(err => {
        console.error('ERROR: statusCode=' + err.statusCode);
        console.dir(JSON.parse(err.body), { depth: null });
    });
}

const client = new Client(configArgs);

const payload = {
    scanData:'AZ0UKhrmatMeKdlfY6b',
    // scanData: $_POST["qrdata"],
    scanReferenceId: 'scanReferId'+date,
    merchantCOE: 'JP',
    ledgerCurrency: 'JPY',
};

merchantScan(payload, { } );

    callback();
};

