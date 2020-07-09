'use strict';
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

const helper = require('./clientHelper.js');

class Client {
    constructor(configArgs) {
        this.configArgs = Object.freeze(configArgs);
    }

    apiCall(options) {
        const preparedOptions = helper.prepareOptions(this.configArgs, options);
        preparedOptions.headers = helper.signHeaders(this.configArgs, preparedOptions);
//        console.log(preparedOptions.headers);
        return helper.invokeApi(this.configArgs, preparedOptions);
    }

    getSignedHeaders(options) {
        const preparedOptions = helper.prepareOptions(this.configArgs, options);
        return helper.signHeaders(this.configArgs, preparedOptions);
    }

}

module.exports = Client;
