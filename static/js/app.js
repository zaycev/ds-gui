"use strict";

var app = angular.module("WebApp", ["ngRoute"])
    .config(["$routeProvider", "$locationProvider",
    function($routeProvider, $locationProvider) {

        $routeProvider.when("/", {
             templateUrl: "/static/html/search-result.html",
             controller: "SeachController"
        });
        $routeProvider.otherwise({redirectTo: "/"});
}]);

angular.module("ng").filter("cut", function () {
    return function (value, wordwise, max, tail) {
        if (!value) return "";
        max = parseInt(max, 10);
        if (!max) return value;
        if (value.length <= max) return value;

        value = value.substr(0, max);
        if (wordwise) {
            var lastspace = value.lastIndexOf(" ");
            if (lastspace != -1) {
                value = value.substr(0, lastspace);
            }
        }
        return value + (tail || " …");
    };
});

app.filter("pagination", function() {
  return function(input, total) {
    total = parseInt(total);
    for (var i=1; i<=total; i++)
      input.push(i);
    return input;
  };
});


//app.factory("SeachService", ["$http", "$location",
//    function($http) {
//        return {
//            find_any: function(keywords) {
//                return $http.get("/find", keywords);
//            }
//        };
//    }
//]);