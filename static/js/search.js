/**
 *
 *
 */

app.controller("SeachController", ["$scope", "$location", "$http", "$timeout",
    function ($scope, $location, $http, $timeout) {

        var index_names = {
            "eng": "English",
            "eng_gen": "English (generalized)",
            "rus": "Russian",
            "rus_gen": "Russian (generalized)",
            "spa": "Spanish"
        };

        var query = $location.search().query;
        var index = $location.search().index;
        var mfreq = $location.search().mfreq;
        var rpage = $location.search().rpage;
        var rtype = $location.search().rtype;
        var debug = $location.search().debug;

        if (typeof query == "undefined") query = "";
        if (typeof index == "undefined") index = "eng";
        if (typeof mfreq == "undefined") mfreq = "0";
        if (typeof rpage == "undefined") rpage = "1";
        if (typeof rtype == "undefined") rtype = "*";

        $scope.query = {
            "query": query,
            "index": index,
            "mfreq": mfreq,
            "rpage": rpage,
            "rtype": rtype,
            "debug": debug,
            "index_name": index_names[index]
        };

        if (query != "") {
            $http({
                method: "GET",
                url: "/find",
                params: {
                    "query": query,
                    "index": index,
                    "mfreq": mfreq,
                    "rpage": rpage,
                    "rtype": rtype
                }
            }).success(function (data, status, headers, config) {
                    $scope.search_result = data;
                    $timeout(function(){
                        $(".show-popover").popover({
                            "html": true
                        });
                    }, 0, false);
            }).error(function (data, status, headers, config) {

            });
        }

        $scope.SetIndex = function(index) {
            $scope.query.index = index;
            $scope.Find();
        };

        $scope.Find = function (page) {
            if (typeof page != "undefined")
                $scope.query.rpage = page;
            else
                $scope.query.rpage = "1";
            console.log("Find");
            $location.path("/").search({
                "query": $scope.query.query,
                "index": $scope.query.index,
                "mfreq": $scope.query.mfreq,
                "rpage": $scope.query.rpage,
                "rtype": $scope.query.rtype
            });
        };

        $scope.ShowRelTypeHelp = function() {
            $("#RelTypeHelp").modal();
        };
        $scope.ShowFreqHelp = function() {
            $("#FreqHelp").modal();
        };


}]);