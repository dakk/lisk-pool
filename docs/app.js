var app = angular.module('delegateApp', []);

app.controller('indexCtrl', function($scope, $http) {
    $scope.accounts = [];
    $scope.lastpayout = 0;
    $scope.nextpayout = 0;

    $http.get ('poollogs.json').then (function (res) {
        $scope.lastpayout = res.data.lastpayout * 1000;
        $scope.nextpayout = moment ($scope.lastpayout).add (1, 'week').valueOf();
        $scope.accounts = [];
        $scope.total = { paid: 0.0, pending: 0.0 };

        for (addr in res.data.accounts) {
            var it = res.data.accounts[addr];
            it['address'] = addr;
            $scope.accounts.push (it);
            $scope.total.paid += res.data.accounts[addr].received;
            $scope.total.pending += res.data.accounts[addr].pending;
        }
    });

    $http.get ('https://wallet.lisknode.io/api/delegates/get?username=dakk').then (function (res) {
        $scope.delegate = res.data.delegate;
    });
});
