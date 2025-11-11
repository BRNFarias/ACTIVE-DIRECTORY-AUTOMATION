db.createUser({
  user: "exporter",
  pwd: "exporter",
  roles: [
    { role: "clusterMonitor", db: "admin" },
    { role: "read", db: "local" }
  ]
});
