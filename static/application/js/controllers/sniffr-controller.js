/**
 * This is free and unencumbered software released into the public domain.
 *
 * Anyone is free to copy, modify, publish, use, compile, sell, or
 * distribute this software, either in source code form or as a compiled
 * binary, for any purpose, commercial or non-commercial, and by any
 * means.
 *
 * In jurisdictions that recognize copyright laws, the author or authors
 * of this software dedicate any and all copyright interest in the
 * software to the public domain. We make this dedication for the benefit
 * of the public at large and to the detriment of our heirs and
 * successors. We intend this dedication to be an overt act of
 * relinquishment in perpetuity of all present and future rights to this
 * software under copyright law.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
 * OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
 * ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 *
 * For more information, please refer to <http://unlicense.org>
 *
 */
"use strict"

websnifferApp.controller("WebSniffer", function ($scope, $http, $location, $cookies, LZString) {
    $scope.static = {
        methods: ["GET", "POST", "HEAD", "DELETE", "PUT", "OPTIONS", "PATCH"]
    };

    /**
     * Form elements
     * @type Object
     */
    $scope.formdata = {
        url: "https://httpbin.org/redirect/5",
        headers: [
            { key: "Accept-Encoding", value: "gzip, deflate" },
            { key: "User-Agent", value: __ua }
        ],
        parameters: [],
        method: $scope.static.methods[0]
    };

    //var urlQuery = $location.search().q;
    //if(angular.isDefined(urlQuery)) {console.log();
    //    var decodedUrlString = LZString.decompressFromBase64(urlQuery);
    //    if(decodedUrlString !== null && angular.isString(decodedUrlString)) {
    //        $scope.formdata = angular.fromJson(decodedUrlString);
    //    }
    //}

    $scope.options = {
        prettyPrint: false,
        showRecaptcha: true,
        showAdvanced: $cookies.get("showAdvanced") == "true" ? true : false
    };

    /**
     *
     */
    $scope.address = null;

    /**
     *
     */
    $scope.messages = null;

    /**
     * Called on form submission.
     * Disallow
     *
     * @param {object} $event Information about the form onsubmit
     * event.
     */
    $scope.checkAddress = function($event) {
        $event.preventDefault();

        var f = document.getElementById("sniff");
        $scope.working = true;

        NProgress.start();

        $http({method: "post", url: f.action, data: $scope.formdata })
            .then(function(response) {
                $scope.messages = null;
                $scope.address = null;
                $scope.working = false;

                if(response.data.sniffed && response.data.sniffed.body) {
                    // Requested URL Content.
                    // Better to transferred as a Base64 encoded string.
                    response.data.sniffed.body = atob(response.data.sniffed.body);
                }

                // Request information
                $scope.address = response.data.sniffed;

                // Any messages that may be required to display
                // In cases of success, hopefuly none! :)
                $scope.messages = response.data.messages;

                $scope.options.showRecaptcha = response.data.showRecaptcha;
            }, function(response) {
                $scope.address = null;
                $scope.messages = [response.data.message];
                $scope.options.showRecaptcha = response.data.showRecaptcha;
                $scope.working = false;
            })
            .then(NProgress.done);
    };

    $scope.keyboard = function($event) {
        var input = document.getElementById("url");
        var focused = document.activeElement;

        if(focused.type != "text" && focused.type != "url" && focused.type != "textarea") {
            if($event.key.toLowerCase() == "r" && $scope.sniff.$valid) {
                $scope.checkAddress($event);
            } else if($event.key.toLowerCase() == "l") {
                input.focus();
                input.selectionStart = input.selectionEnd = input.value.length;
            } else if($event.key.toLowerCase() == "a") {
                $scope.options.showAdvanced = !$scope.options.showAdvanced;
                $cookies.put("showAdvanced", $scope.options.showAdvanced);
            }
        }
    };

    $scope.copyToLocation = function() {
        $scope.formdata.url = $scope.address.information.redirect.url;
    };

    /**
     *
     */
    $scope.prettyPrint = function() {
        prettyPrint();
    };

    /**
     * Generate a reusable link so users can replicate the "sniff" scenario quickly
     */
    $scope.generateLink = function() {
        $scope.generatedLink = LZString.compressToBase64(angular.toJson($scope.formdata));
    };
});