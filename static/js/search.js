/**
 *
 *
 */

app.controller("SeachController", ["$scope", "$location", "$http",
    function ($scope, $location, $http) {

        var query = $location.search().query;
        var store = $location.search().store;
        var mfreq = $location.search().mfreq;

        if (typeof query == "undefined") query = "";
        if (typeof store == "undefined") store = "eng";
        if (typeof mfreq == "undefined") mfreq = "0";


        $scope.query = {
            "query": query,
            "store": store,
            "mfreq": mfreq
        };

        if (query != "") {
            $http({
                method: "GET",
                url: "/find",
                params: {
                    "query": query,
                    "store": store,
                    "mfreq": mfreq
                }
            }).success(function (data, status, headers, config) {
                    $scope.triples = data;
            }).error(function (data, status, headers, config) {

            });
        }

        $scope.Find = function () {
            console.log("Find");
            $location.path("/").search({
                "query": $scope.query.query,
                "store": $scope.query.store,
                "mfreq": $scope.query.mfreq
            });
        };


}]);