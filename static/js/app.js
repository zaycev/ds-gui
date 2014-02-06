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