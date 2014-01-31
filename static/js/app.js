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