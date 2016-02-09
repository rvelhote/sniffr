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

websnifferApp.directive("keyValueTable", function() {
    return {
        restrict: "A",
        templateUrl: "keyvalue-table.html",
        scope: {
            content: "=source",
            title: "@",
            action: "@",
            allowText: "@"
        },
        link: function($scope, $element, $attrs) {
            $scope.displayTextInput = $scope.allowText == "true";

            $scope.$watch("displayTextInput", function(newValue, oldValue) {
                if(newValue === true) {
                    $scope.content = "";
                } else if(oldValue == true && newValue == false) {
                    $scope.content = [];
                }
            });

            $scope.addLine = function() {
                $scope.content.push({ key: "", value: "", disabled: false })
            };

            $scope.removeLine = function(index) {
                if($scope.content.length > 0 && angular.isDefined($scope.content[index])) {
                    $scope.content.splice(index, 1)
                }
            };

            $scope.toggleLine = function(index) {
                if($scope.content.length > 0 && angular.isDefined($scope.content[index])) {
                    $scope.content[index].disabled = !$scope.content[index].disabled;
                }
            };
        }
    };
});
