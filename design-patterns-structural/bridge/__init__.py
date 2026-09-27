"""
Bridge Pattern - two hierarchies that vary independently

Bridge exists when you have two axes of variation that grow on their own:

    abstraction  x  implementor

Two worked examples live here, one per axis:

- ``notification``  message  x  channel
    ``Message`` knows what to say; ``Channel`` knows how to deliver it.
- ``diagram``       shape    x  renderer
    ``Shape`` knows its geometry; ``Renderer`` knows an output format.

The defining rules, both asserted by the test suite:

1. The abstraction *holds* its implementor (composition, not inheritance).
2. The implementor never mentions the abstraction. Its methods take plain
   values, so adding a message type cannot force a change to any channel.
"""
