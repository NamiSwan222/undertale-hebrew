using System.Linq;
EnsureDataLoaded();
foreach (var n in new[]{"obj_shop1","obj_shop2","obj_savepoint"}) {
  var o = Data.GameObjects.ByName(n);
  var rooms = Data.Rooms.Where(r => r.GameObjects.Any(g => g.ObjectDefinition == o)).Select(r => r.Name.Content).Take(40).ToArray();
  Console.WriteLine($"{n}: [{string.Join(",", rooms)}]");
}
